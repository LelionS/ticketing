import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Group
import uuid

User = settings.AUTH_USER_MODEL

class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    code = models.CharField(max_length=30, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()

    department = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    expected_resolution_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Expected date/time the department should resolve this ticket",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tickets_created",
        editable=False,
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_updated",
        editable=False,
    )

    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Generate unique ticket code using date + short UUID
        if not self.code:
            today_str = timezone.now().strftime("%Y%m%d")
            unique_suffix = uuid.uuid4().hex[:6].upper()
            self.code = f"T{today_str}-{unique_suffix}"

        # Set timestamps for resolved/closed
        if self.status == "resolved" and not self.resolved_at:
            self.resolved_at = timezone.now()
        if self.status == "closed" and not self.closed_at:
            self.closed_at = timezone.now()

        super().save(*args, **kwargs)

    def resolve(self):
        self.status = "resolved"
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at"])

    def close(self):
        self.status = "closed"
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at"])

    def is_overdue(self):
        return (
            self.expected_resolution_date
            and self.status not in ["resolved", "closed"]
            and timezone.now() > self.expected_resolution_date
        )
    def overdue_days(self):
        if not self.is_overdue():
            return 0
        return (timezone.now() - self.expected_resolution_date).days

    def __str__(self):
        return f"{self.code} - {self.title}"

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        "Ticket",
        on_delete=models.CASCADE,
        related_name="attachments"
    )
    file = models.FileField(upload_to="ticket_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return f"{self.ticket.code} - {self.filename()}"


class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_comments")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# models.py
from django.db import models


class EmailConfig(models.Model):
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=587)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Encrypt in production
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    default_from_email = models.EmailField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configurations"

    def save(self, *args, **kwargs):
        # Ensure only one active config
        if self.is_active:
            EmailConfig.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

from django.db import models
from django.utils import timezone

class TicketReport(models.Model):
    department = models.ForeignKey(Group, on_delete=models.CASCADE)
    open_count = models.IntegerField(default=0)
    in_progress_count = models.IntegerField(default=0)
    resolved_count = models.IntegerField(default=0)
    closed_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.department.name} Report"

class MyTickets(Ticket):
    class Meta:
        proxy = True
        verbose_name = "My Ticket"
        verbose_name_plural = "My Tickets"

class DepartmentTickets(Ticket):
    class Meta:
        proxy = True
        verbose_name = "Department Ticket"
        verbose_name_plural = "Department Tickets"

class EmailIngestLog(models.Model):
    status = models.CharField(max_length=20)
    payload = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TicketOverdue(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="overdue"
    )

    first_detected_at = models.DateTimeField(null=True, blank=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)

    notification_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_overdue(self):
        return self.ticket.is_overdue()

    def mark_notified(self):
        now = timezone.now()

        if not self.first_detected_at:
            self.first_detected_at = now

        self.last_notified_at = now
        self.notification_count += 1

        self.save(update_fields=[
            "first_detected_at",
            "last_notified_at",
            "notification_count"
        ])

    def __str__(self):
        return f"Overdue: {self.ticket.code}"

