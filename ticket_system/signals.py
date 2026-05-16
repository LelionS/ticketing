# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket, TicketReport

@receiver(post_save, sender=Ticket)
def update_ticket_report(sender, instance, **kwargs):
    if not instance.department:
        return

    report, _ = TicketReport.objects.get_or_create(department=instance.department)

    report.open_count = Ticket.objects.filter(department=instance.department, status="Open").count()
    report.in_progress_count = Ticket.objects.filter(department=instance.department, status="In Progress").count()
    report.resolved_count = Ticket.objects.filter(department=instance.department, status="Resolved").count()
    report.closed_count = Ticket.objects.filter(department=instance.department, status="Closed").count()

    report.save()





from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Ticket, EmailConfig  # adjust if needed
from .utils import should_send_overdue_reminder
from .email_overdue import send_overdue_email


LAST_SENT = {}


@receiver(post_save, sender=Ticket)
def handle_overdue_reminder(sender, instance, **kwargs):
    if instance.status in ["resolved", "closed"]:
        return

    if not instance.expected_resolution_date:
        return

    if timezone.now() <= instance.expected_resolution_date:
        return

    last_sent = LAST_SENT.get(instance.id)

    if should_send_overdue_reminder(instance, last_sent):
        email_config = EmailConfig.objects.first()  # or tenant-specific logic

        if not email_config:
            return

        send_overdue_email(instance, email_config)

        LAST_SENT[instance.id] = timezone.now()
