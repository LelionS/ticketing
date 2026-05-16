from django.contrib import admin
from django.contrib import admin, messages

from ticket_system.email_to_ticket import build_recipients
from .models import PurchaseOrder
from .utils import send_purchase_order_email

from .models import (
    PurchaseOrder,
    PurchaseOrderNote
)


class PurchaseOrderNoteInline(admin.TabularInline):
    model = PurchaseOrderNote
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):

    list_display = (
        "po_number",
        "ticket_code",
        "item_name",
        "quantity",
        "status",
        "created_at",
    )

    readonly_fields = ("po_number",)

    def ticket_code(self, obj):
        return obj.ticket.code

    ticket_code.short_description = "Ticket Code"

    def save_model(self, request, obj, form, change):

        old_status = None

        if change:
            old_status = PurchaseOrder.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        is_new = not change
        status_changed = old_status and old_status != obj.status

        if not is_new and not status_changed:
            return

        recipients = build_recipients(obj.ticket)

        if not recipients:
            self.message_user(
                request,
                "No recipients found for this ticket.",
                level=messages.WARNING
            )
            return

        try:
            send_purchase_order_email(obj, recipients)

            self.message_user(
                request,
                f"Email sent for PO {obj.po_number}",
                level=messages.SUCCESS
            )

        except Exception as e:
            self.message_user(
                request,
                f"Email failed: {str(e)}",
                level=messages.ERROR
            )