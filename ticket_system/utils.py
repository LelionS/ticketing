# utils.py
import socket
from datetime import datetime
from django.utils.html import format_html
from .models import Ticket

# Color mappings for badges
PRIORITY_COLORS = {
    "Low": "#28a745",        # green
    "Medium": "#ffc107",     # yellow
    "High": "#dc3545",       # red
    "Critical": "#6f42c1",   # purple
}

STATUS_COLORS = {
    "Open": "#17a2b8",         # teal
    "In Progress": "#007bff",  # blue
    "Resolved": "#28a745",     # green
    "Closed": "#6c757d",       # gray
}

DEPARTMENT_COLOR = "#6f42c1"  # purple badge for department

def build_ticket_email(ticket: Ticket, recipient_name: str = None, event: str = "created"):
    """
    Build subject and HTML body for a ticket email with:
    - Personalized greeting
    - Time-based greeting
    - Dynamic server IP for admin URL
    - Colored badges for priority, status, department
    - Bold + italic "Please Do Not Reply"
    - Link masked as "Click here"
    """

    # --- Greeting based on server time ---
    hour = datetime.now().hour
    if 5 <= hour < 12:
        base_greeting = "Good morning"
    elif 12 <= hour < 17:
        base_greeting = "Good afternoon"
    elif 17 <= hour < 21:
        base_greeting = "Good evening"
    else:
        base_greeting = "Hello"

    greeting = f"{base_greeting} {recipient_name}" if recipient_name else base_greeting

    # --- Server IP or hostname dynamically ---
    try:
        server_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        server_ip = "localhost:8000"

    ticket_url = f"http://{server_ip}/admin/ticket_system/ticket/{ticket.pk}/change/"

    # --- Badge colors ---
    priority_color = PRIORITY_COLORS.get(ticket.priority, "#6c757d")
    status_color = STATUS_COLORS.get(ticket.status, "#6c757d")
    department_name = ticket.department.name if ticket.department else "N/A"

    if event.lower() == "created":
        subject = f"New Ticket Registered: {ticket.code}"
        body = format_html(
            """
            <p>{greeting}</p>
            <p>A new ticket has been created in the system:</p>
            <ul>
                <li><strong>Ticket Number:</strong> {code}</li>
                <li><strong>Title:</strong> {title}</li>
                <li><strong>Priority:</strong> <span style="color:white; background-color:{priority_color}; padding:2px 6px; border-radius:4px;">{priority}</span></li>
                <li><strong>Status:</strong> <span style="color:white; background-color:{status_color}; padding:2px 6px; border-radius:4px;">{status}</span></li>
                <li><strong>Department:</strong> <span style="color:white; background-color:{department_color}; padding:2px 6px; border-radius:4px;">{department}</span></li>
            </ul>
            <p>View Ticket: <a href="{url}" target="_blank">Click here</a></p>
            <p>Thank you,<br/>Support Team</p>
            """,
            greeting=greeting,
            code=ticket.code,
            title=ticket.title,
            priority=ticket.priority,
            priority_color=priority_color,
            status=ticket.status,
            status_color=status_color,
            department=department_name,
            department_color=DEPARTMENT_COLOR,
            url=ticket_url
        )

    elif event.lower() in ["resolved", "closed"]:
        subject = f"Ticket {event.title()}: {ticket.code}"
        body = format_html(
            """
            <p>{greeting},</p>
            <p>The ticket has been {event}:</p>
            <ul>
                <li><strong>Ticket Number:</strong> {code}</li>
                <li><strong>Title:</strong> {title}</li>
                <li><strong>Status:</strong> <span style="color:white; background-color:{status_color}; padding:2px 6px; border-radius:4px;">{status}</span></li>
            </ul>
            <p><strong><em>Please Do Not Reply</em></strong></p>
            <p>View Ticket: <a href="{url}" target="_blank">Click here</a></p>
            <p>Thank you,<br/>Support Team</p>
            """,
            greeting=greeting,
            event=event,
            code=ticket.code,
            title=ticket.title,
            status=ticket.status,
            status_color=status_color,
            url=ticket_url
        )

    else:
        # generic update
        subject = f"Update on Ticket: {ticket.code}"
        body = format_html(
            """
            <p>{greeting}</p>
            <p>The ticket has been updated:</p>
            <ul>
                <li><strong>Ticket Number:</strong> {code}</li>
                <li><strong>Title:</strong> {title}</li>
                <li><strong>Status:</strong> <span style="color:white; background-color:{status_color}; padding:2px 6px; border-radius:4px;">{status}</span></li>
            </ul>
            <p><strong><em>Please Do Not Reply</em></strong></p>
            <p>View Ticket: <a href="{url}" target="_blank">Click here</a></p>
            <p>Thank you,<br/>Support Team</p>
            """,
            greeting=greeting,
            code=ticket.code,
            title=ticket.title,
            status=ticket.status,
            status_color=status_color,
            url=ticket_url
        )

    return subject, body