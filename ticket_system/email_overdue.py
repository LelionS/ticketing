from django.core.mail import EmailMessage, get_connection


def send_overdue_email(ticket, email_config):
    if not ticket.assigned_to or not ticket.assigned_to.email:
        return

    subject = f"Overdue Ticket Reminder: {ticket.code}"

    message = f"""
Ticket is overdue

Code: {ticket.code}
Title: {ticket.title}
Status: {ticket.status}
Expected Resolution Date: {ticket.expected_resolution_date}

Please take immediate action.
"""

    connection = get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=email_config.host,
        port=email_config.port,
        username=email_config.username,
        password=email_config.password,
        use_tls=email_config.use_tls,
        use_ssl=email_config.use_ssl,
    )

    email = EmailMessage(
        subject,
        message,
        email_config.from_email,
        [ticket.assigned_to.email],
        connection=connection,
    )

    email.send(fail_silently=False)
