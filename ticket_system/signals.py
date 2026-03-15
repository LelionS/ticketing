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