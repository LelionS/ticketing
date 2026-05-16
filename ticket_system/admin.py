from django import forms
from django.contrib import admin
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from .utils import get_outlook_importance
from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib import messages
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
from .models import TicketComment, TicketAttachment

from django.utils.html import format_html
from django.urls import reverse


from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TicketAttachment

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from purchase_orders.models import PurchaseOrder
from django.contrib import admin



from django.contrib import admin
from django.utils.html import format_html

from .models import Ticket

from django.utils.html import format_html
from django.utils.safestring import mark_safe
from purchase_orders.models import PurchaseOrderNote


class PurchaseOrderNotesMixin:

    def purchase_order_notes(self, obj):

        notes = PurchaseOrderNote.objects.filter(
            purchase_order__ticket=obj
        ).select_related("purchase_order").order_by("-created_at")

        if not notes.exists():
            return "No Purchase Order notes."

        html = ""

        for note in notes:
            html += f"""
            <div style="
                margin-bottom:10px;
                padding:12px;
                border:1px solid #ddd;
                border-radius:6px;
                background:#f8f8f8;
            ">
                <strong>{note.purchase_order.po_number}</strong>
                <br><br>

                {note.note}

                <br><br>

                <small>
                    {note.created_at.strftime("%Y-%m-%d %H:%M")}
                </small>
            </div>
            """

        return mark_safe(html)

    purchase_order_notes.short_description = "Purchase Order Notes"

from purchase_orders.models import (
    PurchaseOrder,
    PurchaseOrderNote
)


class PurchaseOrderInline(admin.StackedInline):
    model = PurchaseOrder
    extra = 1

    fields = (
        "po_number",
        "item_name",
        "description",
        "quantity",
        "status",
    )

    readonly_fields = ("po_number",)

    show_change_link = True


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 1

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
from .email_to_ticket import get_active_email_config
from .email_to_ticket import build_recipients

from purchase_orders.utils import send_purchase_order_email


User = get_user_model()


@admin.register(Ticket)
class TicketAdmin(PurchaseOrderNotesMixin, admin.ModelAdmin):
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
        "purchase_order_notes",
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
        (
            "Purchase Order Notes",
            {
                "fields": (
                    "purchase_order_notes",
                )
            },
        ),
    )

    inlines = [TicketCommentInline, TicketAttachmentInline, PurchaseOrderInline]

    
    def save_formset(self, request, form, formset, change):
    """
    Handles inline saving (PurchaseOrder + others).
    This is where inline PurchaseOrders are created.
    """

        instances = formset.save(commit=False)
    
        for obj in instances:
            obj.save()
    
            # -----------------------------
            # PURCHASE ORDER INLINE TRIGGER
            # -----------------------------
            if isinstance(obj, PurchaseOrder):
    
                try:
                    recipients = build_recipients(obj.ticket)
    
                    if recipients:
                        send_purchase_order_email(
                            obj,
                            recipients,
                            event_type="created"
                        )
    
                except Exception as e:
                    self.message_user(
                        request,
                        f"PO email failed: {str(e)}",
                        level=messages.ERROR
                    )
    
        formset.save_m2m()


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
        from django.contrib import messages

        is_new = not change

        old_status = None
        if change:
            old_status = Ticket.objects.get(pk=obj.pk).status

        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

        status_changed = old_status and old_status != obj.status

        if not is_new and not status_changed:
            return

    # -----------------------------
    # ADD THIS (MISSING PARTS)
    # -----------------------------
        email_config = get_active_email_config()

        if not email_config:
            self.message_user(request, "No active email config", messages.ERROR)
            return

        recipients_unique = build_recipients(obj)

        if not recipients_unique:
            return

        event_type = "created" if is_new else obj.status.lower()

    # -----------------------------
    # YOUR LOOP GOES HERE (UNCHANGED)
    # -----------------------------
        for email_address, name in recipients_unique:
            try:
                subject, body_html = build_ticket_email(
                    obj,
                    recipient_name=name,
                    event=event_type
                )
    
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=email_config.host,
                    port=email_config.port,
                    username=email_config.username,
                    password=email_config.password,
                    use_tls=email_config.use_tls,
                    use_ssl=email_config.use_ssl,
                )

                email_msg = EmailMessage(
                    subject=subject,
                    body=body_html,
                    from_email=email_config.default_from_email,
                    to=[email_address],
                    connection=connection,
                )

                email_msg.content_subtype = "html"
                email_msg.extra_headers = get_outlook_importance(obj)

                email_msg.send(fail_silently=False)

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
       
        from django.utils import timezone
        from .models import TicketOverdue

        if obj.is_overdue():
            overdue_obj, _ = TicketOverdue.objects.get_or_create(ticket=obj)

            if not overdue_obj.last_notified_at or (
                timezone.now() - overdue_obj.last_notified_at
            ).days >= 1:

                for email_address, name in recipients_unique:
                    try:
                        subject, body_html = build_ticket_email(
                            obj,
                            recipient_name=name,
                            event="overdue"
                        )

                        connection = get_connection(
                            backend='django.core.mail.backends.smtp.EmailBackend',
                            host=email_config.host,
                            port=email_config.port,
                            username=email_config.username,
                            password=email_config.password,
                            use_tls=email_config.use_tls,
                            use_ssl=email_config.use_ssl,
                        )

                        email_msg = EmailMessage(
                           subject=subject,
                            body=body_html,
                            from_email=email_config.default_from_email,
                            to=[email_address],
                            connection=connection,
                        )
    
                        email_msg.content_subtype = "html"
                        email_msg.extra_headers = get_outlook_importance(obj)
    
                        email_msg.send(fail_silently=False)

                    except Exception as e:
                        self.message_user(
                            request,
                            f"Overdue email failed to {email_address}: {str(e)}",
                            level=messages.ERROR
                        )

                overdue_obj.mark_notified()
        
                self.message_user(
                    request,
                    f"Overdue reminder sent for ticket '{obj.code}'.",
                    level=messages.WARNING
                )
# admin.py
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage, get_connection
from .models import EmailConfig

from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.core.mail import EmailMessage, get_connection
from django import forms
from .models import EmailConfig


from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.core.mail import EmailMessage, get_connection
from django import forms
from .models import EmailConfig


@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'host')
    change_form_template = "admin/it/emailconfig/change_form.html"

    # Custom form inside admin to make password optional
    class EmailConfigAdminForm(forms.ModelForm):
        class Meta:
            model = EmailConfig
            fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['password'].required = False
            self.fields['password'].widget.attrs['placeholder'] = 'Optional if no auth'

    form = EmailConfigAdminForm

    # Add custom URL for SMTP testing
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

    # SMTP test view
    def test_smtp_view(self, request, config_id):
        config = EmailConfig.objects.get(pk=config_id)

        if request.method == "POST":
            test_email = request.POST.get("test_email")
            result = {"success": False, "message": ""}

            try:
                connection_params = {
                    "backend": 'django.core.mail.backends.smtp.EmailBackend',
                    "host": config.host,
                    "port": config.port,
                    "use_tls": config.use_tls,
                    "use_ssl": config.use_ssl,
                }

                # Include username/password only if provided
                if config.username and config.password:
                    connection_params["username"] = config.username
                    connection_params["password"] = config.password

                connection = get_connection(**connection_params)

                email = EmailMessage(
                    subject="SMTP Configuration Test",
                    body="This is a test email from Ticket System SMTP configuration.",
                    from_email=config.default_from_email,
                    to=[test_email],
                    connection=connection,
                )
                email.extra_headers = {
                    "Importance": "High",
                    "X-Priority": "1",
                    "X-MSMail-Priority": "High",
                }

                email.send(fail_silently=False)
                result["success"] = True
                result["message"] = f"Test email sent successfully to {test_email}"
                self.message_user(request, result["message"], level=messages.SUCCESS)
            except Exception as e:
                result["message"] = f"SMTP Test Failed: {str(e)}"
                self.message_user(request, result["message"], level=messages.ERROR)

            # Render a simple result page
            return render(
                request,
                "admin/it/emailconfig/test_smtp_result.html",
                {"config": config, "result": result},
            )

        context = {"config": config}
        return render(request, "admin/it/emailconfig/test_smtp.html", context)

    # Add Test SMTP button in change view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj:
            extra_context = extra_context or {}
            extra_context['test_smtp_url'] = reverse(
                'admin:it_emailconfig_test_smtp', args=[obj.pk]
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import TicketReport, Ticket
from django.core.serializers.json import DjangoJSONEncoder
import json

from django.utils import timezone
from datetime import timedelta

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
            tickets = Ticket.objects.filter(
                department__in=request.user.groups.all()
            )

        # ✅ STATUS (FIXED)
        STATUS_MAP = {
            "Open": "open",
            "In Progress": "in_progress",
            "Resolved": "resolved",
            "Closed": "closed",
        }

        status_labels = list(STATUS_MAP.keys())
        status_counts = [
            tickets.filter(status=STATUS_MAP[label]).count()
            for label in status_labels
        ]

        # PRIORITY
        priority_labels = ["High", "Medium", "Low"]
        priority_counts = [
            tickets.filter(priority=p).count()
            for p in priority_labels
        ]

        # TREND (last 8 weeks)
        today = timezone.now()
        
        start_of_current_week = today - timedelta(days=today.isoweekday() - 1)
        
        weeks, week_counts = [],[]

        for i in range(8):
            start = today - timedelta(weeks=i + 1)
            end = start + timedelta(weeks=1)
            count = tickets.filter(
                created_at__range=(start, end)
            ).count()
            
            
            weeks.append(start.strftime("Week %W"))
            week_counts.append(count)

        weeks.reverse()
        week_counts.reverse()

        # DEPARTMENT
        dept_data = tickets.values('department__name').annotate(total=Count('id'))
        departments = [d['department__name'] for d in dept_data]
        dept_counts = [d['total'] for d in dept_data]

        # RESOLUTION TIME
        resolution_priorities = priority_labels
        avg_resolution = []

        for p in resolution_priorities:
            qs = tickets.filter(
                priority=p,
                resolved_at__isnull=False
            )

            if qs.exists():
                avg = sum([
                    (t.resolved_at - t.created_at).total_seconds() / 3600
                    for t in qs
                ]) / qs.count()
            else:
                avg = 0

            avg_resolution.append(round(avg, 2))

        # ✅ TICKETS FOR MODALS (FIXED STATUS)
        tickets_by_status = {
            label: [
                {"title": t.title, "id": t.id}
                for t in tickets.filter(status=STATUS_MAP[label])
            ]
            for label in status_labels
        }

        tickets_by_priority = {
            p: [
                {"title": t.title, "id": t.id}
                for t in tickets.filter(priority=p)
            ]
            for p in priority_labels
        }

        

        tickets_by_week = {} 
        for i, w in enumerate(weeks): 
            start = today - timedelta(weeks=8 - i) 
            end = today - timedelta(weeks=7 - i) 

            tickets_by_week[w] = [ 
                {"title": t.title, "id": t.id} 
                for t in tickets.filter(
                    created_at__range=(start, end)
                ) 
            ]


        tickets_by_department = {}
        for d in departments:
            tickets_by_department[d] = [
                {"title": t.title, "id": t.id}
                for t in tickets.filter(department__name=d)
            ]

        extra_context = extra_context or {}
        extra_context.update({
            "status_labels": json.dumps(status_labels),
            "status_counts": status_counts,

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
