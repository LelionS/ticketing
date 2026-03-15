from django import forms
from django.contrib import admin
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Ticket, TicketComment, MyTickets, DepartmentTickets
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import TicketComment

User = get_user_model()

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import TicketComment

class TicketCommentInlineForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ("message",)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)  # always capture request
        super().__init__(*args, **kwargs)
        # Hide message field if this comment already exists (i.e., saved)
        if self.instance and self.instance.pk:
            self.fields["message"].widget = forms.HiddenInput()
            self.fields["message"].required = False

    def save(self, commit=True):
        # Always assign sender for new comments
        if not self.instance.sender_id and self.request:
            self.instance.sender = self.request.user
        return super().save(commit=commit)

class TicketCommentInline(admin.StackedInline):
    model = TicketComment
    form = TicketCommentInlineForm
    extra = 0
    max_num = 100
    readonly_fields = ("chat_display",)
    fieldsets = ((None, {"fields": ("chat_display", "message")}),)

    def chat_display(self, obj):
        alignment_class = "recipient"
        if hasattr(obj, "_request") and obj.sender_id == obj._request.user.id:
            alignment_class = "sender"

        status_badge = format_html(
            '<span style="background-color:{}; color:white; padding:2px 4px; border-radius:4px;">{}</span>',
            "#17a2b8" if obj.ticket.status == "open" else "#28a745",
            obj.ticket.get_status_display()
        )

        priority_color = {
            "low": "#6c757d",
            "medium": "#007bff",
            "high": "#ffc107",
            "critical": "#dc3545",
        }.get(obj.ticket.priority, "#007bff")

        priority_badge = format_html(
            '<span style="background-color:{}; color:white; padding:2px 4px; border-radius:4px; margin-left:4px;">{}</span>',
            priority_color,
            obj.ticket.get_priority_display()
        )

        return format_html(
            '<div class="chat-bubble {}">'
            '<strong>{}</strong> <span style="font-size:0.8em; color:#666;">{}</span>'
            '<div style="margin-top:4px;">{}</div>'
            '<div style="margin-top:4px;">{} {}</div>'
            '</div>',
            alignment_class,
            obj.sender.username if obj.sender else "-",
            obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else "-",
            obj.message,
            status_badge,
            priority_badge
        )

    chat_display.short_description = "Chat"

    def get_queryset(self, request):
        # Reverse order: latest message first
        qs = super().get_queryset(request).order_by("-created_at")
        for obj in qs:
            obj._request = request
        return qs

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        class FormSetWithRequest(formset):
            def __init__(self2, *args, **kwargs2):
                super().__init__(*args, **kwargs2)
                for form in self2.forms:
                    form.request = request
        return FormSetWithRequest

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.sender_id:
                obj.sender = request.user
            obj.save()
        formset.save_m2m()

    class Media:
        js = ('ticket_system/js/chat_admin.js',)
        css = {'all': ('ticket_system/css/chat_admin.css',)}

from django.contrib import admin, messages
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import EmailMessage, get_connection
from django.shortcuts import redirect
from .models import Ticket, TicketComment, EmailConfig
from django.core.mail import EmailMessage, get_connection
from .utils import build_ticket_email  # your utility function for email content

User = get_user_model()


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "department",
        "priority",
        "status",
        "expected_resolution_date",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
        "resolved_at",
        "closed_at",
    )

    list_filter = (
        "status",
        "priority",
        "department",
        "created_at",
        "expected_resolution_date",
    )

    search_fields = (
        "code",
        "title",
        "description",
        "created_by__username",
        "updated_by__username",
    )

    readonly_fields = (
        "code",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "resolved_at",
        "closed_at",
    )

    fieldsets = (
        (
            "Ticket Info",
            {
                "fields": (
                    "code",
                    "title",
                    "description",
                    "department",
                    "priority",
                    "status",
                    "expected_resolution_date",
                    "created_by",
                    "updated_by",
                )
            },
        ),
        (
            "Lifecycle",
            {
                "fields": (
                    "resolved_at",
                    "closed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = [TicketCommentInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs

        return qs.filter(
            Q(department__in=request.user.groups.all()) |
            Q(created_by=request.user)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "created_by" and not request.user.is_superuser:
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        is_new = not obj.pk

        if is_new:
            obj.created_by = request.user

        obj.updated_by = request.user

        if obj.status == "resolved" and not obj.resolved_at:
            obj.resolved_at = timezone.now()

        if obj.status == "closed" and not obj.closed_at:
            obj.closed_at = timezone.now()

        super().save_model(request, obj, form, change)

        # --- Send email ---
        email_config = EmailConfig.objects.filter(is_active=True).first()
        if not email_config:
            self.message_user(request, "No active Email Configuration found, email not sent.", level=messages.WARNING)
            return

        # Build recipient list: ticket creator + department users
        recipients = []
        if obj.created_by and obj.created_by.email:
            recipients.append((obj.created_by.email, obj.created_by.get_full_name() or obj.created_by.username))
        if obj.department:
            for user in obj.department.user_set.exclude(email=""):
                recipients.append((user.email, user.get_full_name() or user.username))
        # Remove duplicates by email
        seen = set()
        recipients_unique = []
        for email, name in recipients:
            if email not in seen:
                recipients_unique.append((email, name))
                seen.add(email)

        if not recipients_unique:
            return

        # Determine event type
        event_type = "created" if is_new else obj.status.lower()  # "resolved" or "closed" or "open"

        for email_address, name in recipients_unique:
            try:
                subject, body_html = build_ticket_email(obj, recipient_name=name, event=event_type)

                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=email_config.host,
                    port=email_config.port,
                    username=email_config.username,
                    password=email_config.password,
                    use_tls=email_config.use_tls,
                    use_ssl=email_config.use_ssl,
                )

                email = EmailMessage(
                    subject=subject,
                    body=body_html,
                    from_email=email_config.default_from_email,
                    to=[email_address],
                    connection=connection,
                )
                email.content_subtype = "html"
                email.send(fail_silently=False)
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to send email to {email_address}: {str(e)}",
                    level=messages.ERROR
                )

        self.message_user(
            request,
            f"Ticket '{obj.code}' notification emails sent successfully.",
            level=messages.SUCCESS
        )
        
# admin.py
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage, get_connection
from .models import EmailConfig

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'host')
    change_form_template = "admin/it/emailconfig/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:config_id>/test-smtp/',
                self.admin_site.admin_view(self.test_smtp_view),
                name='it_emailconfig_test_smtp',
            ),
        ]
        return custom_urls + urls

    def test_smtp_view(self, request, config_id):
        config = EmailConfig.objects.get(pk=config_id)

        if request.method == "POST":
            test_email = request.POST.get("test_email")
            try:
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=config.host,
                    port=config.port,
                    username=config.username,
                    password=config.password,
                    use_tls=config.use_tls,
                    use_ssl=config.use_ssl,
                )
                email = EmailMessage(
                    subject="SMTP Configuration Test",
                    body="This is a test email from Ticket System SMTP configuration.",
                    from_email=config.default_from_email,
                    to=[test_email],
                    connection=connection,
                )
                email.send(fail_silently=False)
                self.message_user(
                    request,
                    f"Test email sent successfully to {test_email}",
                    level=messages.SUCCESS,
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"SMTP Test Failed: {str(e)}",
                    level=messages.ERROR,
                )
            return redirect(f"../../{config_id}/change/")

        context = {
            "config": config,
        }
        return render(request, "admin/it/emailconfig/test_smtp.html", context)
        
from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import TicketReport, Ticket
from django.core.serializers.json import DjangoJSONEncoder
import json

from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Ticket, TicketReport

@admin.register(TicketReport)
class TicketReportAdmin(admin.ModelAdmin):
    list_display = (
        'department',
        'open_count',
        'in_progress_count',
        'resolved_count',
        'closed_count',
        'last_updated'
    )

    readonly_fields = (
        'open_count',
        'in_progress_count',
        'resolved_count',
        'closed_count',
        'last_updated'
    )

    change_list_template = "admin/ticket_system/ticketreport_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(department__in=request.user.groups.all())

    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            tickets = Ticket.objects.all()
        else:
            tickets = Ticket.objects.filter(department__in=request.user.groups.all())

        # STATUS & PRIORITY
        status_labels = ["Open", "In Progress", "Resolved", "Closed"]
        status_counts = [tickets.filter(status=s).count() for s in status_labels]

        priority_labels = ["High", "Medium", "Low"]
        priority_counts = [tickets.filter(priority=p).count() for p in priority_labels]

        # TREND (last 8 weeks)
        today = timezone.now()
        weeks, week_counts = [], []
        for i in range(8):
            start = today - timedelta(weeks=i+1)
            end = today - timedelta(weeks=i)
            count = tickets.filter(created_at__range=(start, end)).count()
            weeks.append(start.strftime("Week %W"))
            week_counts.append(count)
        weeks.reverse(); week_counts.reverse()

        # DEPARTMENT
        dept_data = tickets.values('department__name').annotate(total=Count('id'))
        departments = [d['department__name'] for d in dept_data]
        dept_counts = [d['total'] for d in dept_data]

        # RESOLUTION TIME
        resolution_priorities = priority_labels
        avg_resolution = []
        for p in resolution_priorities:
            qs = tickets.filter(priority=p, resolved_at__isnull=False)
            if qs.exists():
                avg = sum([(t.resolved_at - t.created_at).total_seconds()/3600 for t in qs])/qs.count()
            else:
                avg = 0
            avg_resolution.append(round(avg,2))

        # TICKETS BY CATEGORY for modal
        tickets_by_status = {s: [{"title": t.title, "id": t.id} for t in tickets.filter(status=s)] for s in status_labels}
        tickets_by_priority = {p: [{"title": t.title, "id": t.id} for t in tickets.filter(priority=p)] for p in priority_labels}
        tickets_by_week = {}
        for i, w in enumerate(weeks):
            start = today - timedelta(weeks=8-i)
            end = today - timedelta(weeks=7-i)
            tickets_by_week[w] = [{"title": t.title, "id": t.id} for t in tickets.filter(created_at__range=(start,end))]
        tickets_by_department = {}
        for d in departments:
            tickets_by_department[d] = [{"title": t.title, "id": t.id} for t in tickets.filter(department__name=d)]

        extra_context = extra_context or {}
        extra_context.update({
            "status_labels": json.dumps(status_labels),          # JS chart
            "status_counts": status_counts,                       # Python list for template
            "priority_labels": json.dumps(priority_labels),
            "priority_counts": priority_counts,
            "weeks": json.dumps(weeks),
            "week_counts": week_counts,
            "departments": json.dumps(departments),
            "dept_counts": dept_counts,
            "resolution_priorities": json.dumps(resolution_priorities),
            "avg_resolution": avg_resolution,
            "tickets_by_status": json.dumps(tickets_by_status, cls=DjangoJSONEncoder),
            "tickets_by_priority": json.dumps(tickets_by_priority, cls=DjangoJSONEncoder),
            "tickets_by_week": json.dumps(tickets_by_week, cls=DjangoJSONEncoder),
            "tickets_by_department": json.dumps(tickets_by_department, cls=DjangoJSONEncoder),
        })

        return super().changelist_view(request, extra_context=extra_context)

@admin.register(MyTickets)
class MyTicketsAdmin(TicketAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(created_by=request.user)

@admin.register(DepartmentTickets)
class DepartmentTicketsAdmin(TicketAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        
        return qs.filter(department__in=request.user.groups.all())