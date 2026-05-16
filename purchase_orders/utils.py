from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string

from ticket_system.models import EmailConfig


def get_active_email_config():
    return EmailConfig.objects.filter(is_active=True).first()


def build_purchase_order_email(po, recipient_name="User"):

    latest_note = po.notes.order_by("-created_at").first()

    subject = f"Purchase Order Update - {po.po_number} ({po.status.upper()})"

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial;">

        <div style="max-width:700px;margin:auto;padding:20px;border:1px solid #ddd;">

            <h2>Purchase Order Update</h2>

            <p>Hello {recipient_name},</p>

            <p>
                Update on Purchase Order linked to ticket:
                <strong>{po.ticket.code}</strong>
            </p>

            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="border:1px solid #ddd;padding:8px;"><b>PO Number</b></td>
                    <td style="border:1px solid #ddd;padding:8px;">{po.po_number}</td>
                </tr>

                <tr>
                    <td style="border:1px solid #ddd;padding:8px;"><b>Item</b></td>
                    <td style="border:1px solid #ddd;padding:8px;">{po.item_name}</td>
                </tr>

                <tr>
                    <td style="border:1px solid #ddd;padding:8px;"><b>Quantity</b></td>
                    <td style="border:1px solid #ddd;padding:8px;">{po.quantity}</td>
                </tr>

                <tr>
                    <td style="border:1px solid #ddd;padding:8px;"><b>Status</b></td>
                    <td style="border:1px solid #ddd;padding:8px;">{po.get_status_display()}</td>
                </tr>

                <tr>
                    <td style="border:1px solid #ddd;padding:8px;"><b>Description</b></td>
                    <td style="border:1px solid #ddd;padding:8px;">{po.description or ''}</td>
                </tr>
            </table>
"""

    if latest_note:
        body_html += f"""
        <div style="
            margin-top:20px;
            padding:12px;
            background:#f5f5f5;
            border-left:4px solid #333;
        ">
            <b>Latest Note</b><br><br>
            {latest_note.note}
        </div>
        """

    body_html += """
            <p style="margin-top:30px;">
                Regards,<br>
                Service Desk System
            </p>

        </div>

    </body>
    </html>
    """

    return subject, body_html


def send_purchase_order_email(po, recipients):

    email_config = get_active_email_config()

    if not email_config:
        return False

    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=email_config.host,
        port=email_config.port,
        username=email_config.username,
        password=email_config.password,
        use_tls=email_config.use_tls,
        use_ssl=email_config.use_ssl,
    )

    for email_address, name in recipients:

        subject, body_html = build_purchase_order_email(
            po,
            recipient_name=name
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

    return True