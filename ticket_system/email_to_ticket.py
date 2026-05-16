import email
from email.utils import getaddresses

from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage, get_connection

from .models import Ticket, EmailConfig
from .utils import build_ticket_email, get_outlook_importance


# -----------------------------
# Get active email config
# -----------------------------
def get_active_email_config():
    return EmailConfig.objects.filter(is_active=True).first()


# -----------------------------
# Get system emails dynamically
# -----------------------------
def get_system_emails():
    config = get_active_email_config()
    emails = set()

    if config:
        if config.default_from_email:
            emails.add(config.default_from_email.lower())
        if config.username:
            emails.add(config.username.lower())

    return emails


# -----------------------------
# Parse email
# -----------------------------
def parse_email(msg):
    subject = msg.get("subject", "").strip()
    from_email = email.utils.parseaddr(msg.get("from"))[1].lower()

    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="ignore")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="ignore")

    return {
        "subject": subject or "No Subject",
        "from_email": from_email,
        "body": body.strip(),
    }


# -----------------------------
# Extract recipients
# -----------------------------
def extract_recipients(msg):
    to_emails = [e[1].lower() for e in getaddresses(msg.get_all("to", []))]
    cc_emails = [e[1].lower() for e in getaddresses(msg.get_all("cc", []))]
    return to_emails, cc_emails


# -----------------------------
# Resolve department (Group)
# -----------------------------
def resolve_department(to_emails, cc_emails, system_emails):
    ordered = [
        e for e in (to_emails + cc_emails)
        if e and e not in system_emails
    ]

    if not ordered:
        return None

    users = User.objects.filter(email__in=ordered).prefetch_related("groups")
    user_map = {u.email.lower(): u for u in users}

    for email_addr in ordered:
        user = user_map.get(email_addr)
        if user and user.groups.exists():
            return user.groups.first()

    return None


# -----------------------------
# Build recipients
# -----------------------------
def build_recipients(ticket):
    from django.contrib.auth.models import User

    recipients = []

    # requester
    if ticket.created_by and ticket.created_by.email:
        user = ticket.created_by

        full_name = f"{user.first_name} {user.last_name}".strip()
        name = full_name if full_name else user.username

        recipients.append((user.email, name))

    # department users
    if ticket.department:
        users = User.objects.filter(groups=ticket.department)

        for user in users:
            if user.email:
                full_name = f"{user.first_name} {user.last_name}".strip()
                name = full_name if full_name else user.username

                recipients.append((user.email, name))

    # remove duplicates
    seen = set()
    unique = []

    for email, name in recipients:
        if email not in seen:
            seen.add(email)
            unique.append((email, name))

    return unique

# -----------------------------
# Send notifications
# -----------------------------
def send_notifications(ticket, recipients, is_new=True):
    if not recipients:
        return

    email_config = get_active_email_config()
    if not email_config:
        raise Exception("No active EmailConfig found")

    event_type = "created" if is_new else ticket.status.lower()

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
        subject, body_html = build_ticket_email(
            ticket,
            recipient_name=name,
            event=event_type
        )

        email_msg = EmailMessage(
            subject=subject,
            body=body_html,
            from_email=email_config.default_from_email,
            to=[email_address],
            connection=connection,
        )

        email_msg.content_subtype = "html"
        email_msg.extra_headers = get_outlook_importance(ticket)

        email_msg.send(fail_silently=False)


# -----------------------------
# Main entry point
# -----------------------------
from .models import EmailIngestLog

def process_email(msg):
    try:
        EmailIngestLog.objects.create(
            status="STARTED",
            payload=str(msg)[:1000]
        )

        parsed = parse_email(msg)

        EmailIngestLog.objects.create(
            status="PARSED",
            payload=str(parsed)
        )

        system_emails = get_system_emails()

        if parsed["from_email"] in system_emails:
            EmailIngestLog.objects.create(status="BLOCKED_SYSTEM_EMAIL")
            return None

        to_emails, cc_emails = extract_recipients(msg)

        user = User.objects.filter(email__iexact=parsed["from_email"]).first()

        if not user:
            EmailIngestLog.objects.create(status="USER_NOT_FOUND")

        department = user.groups.first() if user else None

        if not department:
            department = Group.objects.filter(name__iexact="Support").first()

        ticket = Ticket.objects.create(
            title=parsed["subject"],
            description=parsed["body"],
            created_by=user,
            department=department,
            status="open"
        )

        EmailIngestLog.objects.create(
            status="TICKET_CREATED",
            payload=ticket.code
        )

        recipients = build_recipients(ticket)
        send_notifications(ticket, recipients, is_new=True)

        return ticket

    except Exception as e:
        EmailIngestLog.objects.create(
            status="ERROR",
            error=str(e)
        )
        return None
