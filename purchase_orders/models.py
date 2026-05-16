import uuid

from django.db import models
from django.utils import timezone

from ticket_system.models import Ticket


class PurchaseOrder(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("ordered", "Ordered"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    po_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="purchase_orders"
    )

    item_name = models.CharField(max_length=255)

    description = models.TextField(
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.po_number:
            today = timezone.now().strftime("%Y%m%d")
            unique = uuid.uuid4().hex[:6].upper()
            self.po_number = f"PO{today}-{unique}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number} - {self.ticket.code}"


class PurchaseOrderNote(models.Model):

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    note = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purchase_order.po_number} Note"