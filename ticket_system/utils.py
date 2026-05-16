# utils.py

import socket
import re
from django.conf import settings
from datetime import datetime
from .models import Ticket

# --- Color mappings (kept for UI/admin usage elsewhere) ---
PRIORITY_COLORS = {
    "Low": "#28a745",
    "Medium": "#ffc107",
    "High": "#dc3545",
    "Critical": "#6f42c1",
}

STATUS_COLORS = {
    "Open": "#17a2b8",
    "In Progress": "#007bff",
    "Resolved": "#28a745",
    "Closed": "#6c757d",
}

DEPARTMENT_COLOR = "#6f42c1"


# --- Helpers ---
def strip_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    return re.sub(r"<.*?>", "", raw_text).strip()

def get_outlook_importance(ticket):
    """
    Returns Outlook email headers based on ticket priority.
    Only High/Critical get High Importance flag.
    """

    priority = getattr(ticket, "priority", "").lower()

    if priority in ["high", "critical"]:
        return {
            "Importance": "High",
            "X-Priority": "1",
            "X-MSMail-Priority": "High",
        }

    return {}

def get_server_url(ticket: Ticket) -> str:
    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")

    return f"{base_url}/admin/ticket_system/ticket/{ticket.pk}/change/"

def get_time_greeting(name: str = None):
    hour = datetime.now().hour
    if 5 <= hour < 12:
        base = "Good morning"
    elif 12 <= hour < 17:
        base = "Good afternoon"
    elif 17 <= hour < 21:
        base = "Good evening"
    else:
        base = "Hello"

    return f"{base}{' ' + name if name else ''}"


def _safe_name(name):
    return name.strip() if name else "Hello"


def _base_ticket_block(ticket):
    return f"""Ticket: {ticket.code}
Title: {ticket.title}
Priority: {ticket.priority}
Status: {ticket.status}
Department: {ticket.department}
"""


def _description(ticket):
    return strip_html(getattr(ticket, "description", "")) or "No details provided"


def _ticket_url(ticket_url, ticket):
    return ticket_url or get_server_url(ticket)


# --- CREATED ---
def build_created_email(ticket, greeting=None, ticket_url=None, recipient_name=None):
    subject = f"Ticket Created: {ticket.code}"

    body = f"""
    <html>
        <body style="font-family: 'Raleway', Arial, Helvetica, sans-serif; font-size: 14px; color: #333;">

            <p>Dear {_safe_name(recipient_name)},</p>

            <p>Your request is now an active ticket and has been allocated to the designated department for handling. This update has been shared with both the originating user and the assigned team to ensure clear communication and accountability.</p>

            <p>
                <strong>Ticket:</strong> {ticket.code}<br>
                <strong>Title:</strong> {ticket.title}<br>
                <strong>Priority:</strong> {ticket.priority}<br>
                <strong>Status:</strong> {ticket.status}<br>
                <strong>Department:</strong> {ticket.department}
            </p>

            <p>
                <strong>Description:</strong><br>
                {_description(ticket)}
            </p>

            <p>
                You can view it here:<br>
                <a href="{_ticket_url(ticket_url, ticket)}">
                    Click here
                </a>
            </p>

            <p><strong>Please do not reply</strong></p>

        </body>
    </html>
    """

    return subject, body


# --- UPDATED ---
def build_updated_email(ticket, greeting=None, ticket_url=None, recipient_name=None):
    subject = f"Ticket Updated: {ticket.code}"

    body = f"""
    <html>
        <body style="font-family: 'Raleway', Arial, Helvetica,sans-serif; font-size: 14px;">
            <p>Dear {_safe_name(recipient_name)},</p>

            <p>Your ticket has been revised with the latest status update and any associated notes from the handling team. Both the requester and the responsible department have been notified to ensure proper communication flow.</p>

            <p>
                <strong>Ticket:</strong> {ticket.code}<br>
                <strong>Title:</strong> {ticket.title}<br>
                <strong>Priority:</strong> {ticket.priority}<br>
                <strong>Status:</strong> {ticket.status}<br>
                <strong>Department:</strong> {ticket.department}
            </p>

            <p>
                <strong>Latest update:</strong><br>
                {_description(ticket)}
            </p>

            <p>
                You can view it here:<br>
                    <a href="{_ticket_url(ticket_url, ticket)}">
                        Click here
                    </a>
            </p>

            <p><strong>Please do not reply</strong></p>
        </body>
    </html>
    """

    return subject, body


# --- RESOLVED ---
def build_resolved_email(ticket, greeting=None, ticket_url=None, recipient_name=None):
    subject = f"Ticket Resolved: {ticket.code}"

    body = f"""
    <html>
        <body style="font-family: 'Raleway', Arial, Helvetica, sans-serif; font-size: 14px; color: #333;">

            <p>Dear {_safe_name(recipient_name)},</p>

            <p>Your ticket has been resolved by the assigned department after all required actions were completed. This update has been shared with both the requester and the responsible team. If you are the requester, please proceed to close the ticket if the resolution meets your expectations.</p>

            <p>
                <strong>Ticket:</strong> {ticket.code}<br>
                <strong>Title:</strong> {ticket.title}<br>
                <strong>Priority:</strong> {ticket.priority}<br>
                <strong>Status:</strong> {ticket.status}<br>
                <strong>Department:</strong> {ticket.department}
            </p>

            <p>
                <strong>Here’s what was noted:</strong><br>
                {_description(ticket)}
            </p>

            <p>
                You can view it here:<br>
                <a href="{_ticket_url(ticket_url, ticket)}">
                    Click here
                </a>
            </p>

            <p><strong>Please do not reply</strong></p>

        </body>
    </html>
    """

    return subject, body

# --- CLOSED ---
def build_closed_email(ticket, greeting=None, ticket_url=None, recipient_name=None):
    subject = f"Ticket Closed: {ticket.code}"

    body = f"""
    <html>
        <body style="font-family: 'Raleway', Arial, Helvetica, sans-serif; font-size: 14px; color: #333;">

            <p>Dear {_safe_name(recipient_name)},</p>

            <p>Your ticket has been successfully closed following confirmation that the issue has been fully resolved. This closure has been shared with both the requester and the assigned department for record and tracking purposes.</p>

            <p>
                <strong>Ticket:</strong> {ticket.code}<br>
                <strong>Title:</strong> {ticket.title}<br>
                <strong>Priority:</strong> {ticket.priority}<br>
                <strong>Status:</strong> {ticket.status}<br>
                <strong>Department:</strong> {ticket.department}
            </p>

            <p>
                <strong>Here’s what was noted:</strong><br>
                {_description(ticket)}
            </p>

            <p>
                You can view it here:<br>
                <a href="{_ticket_url(ticket_url, ticket)}">
                    Click here
                </a>
            </p>

            <p><strong>Please do not reply</strong></p>

        </body>
    </html>
    """

    return subject, body

# --- Dispatcher (safe backward compatibility) ---
def build_ticket_email(ticket, event="created", greeting=None, ticket_url=None, recipient_name=None):
    mapping = {
        "created": build_created_email,
        "updated": build_updated_email,
        "resolved": build_resolved_email,
        "closed": build_closed_email,
    }

    handler = mapping.get(event, build_updated_email)

    return handler(
        ticket,
        greeting=greeting,
        ticket_url=ticket_url,
        recipient_name=recipient_name,
    )



# --- overdue scheduler ---

from django.utils import timezone
from datetime import timedelta


def get_overdue_days(ticket):
    if not ticket.expected_resolution_date:
        return None
    return (timezone.now() - ticket.expected_resolution_date).days


def should_send_overdue_reminder(ticket, last_sent_at=None):
    if ticket.status in ["resolved", "closed"]:
        return False

    overdue_days = get_overdue_days(ticket)
    if overdue_days is None or overdue_days < 0:
        return False

    now = timezone.now()

    if not last_sent_at:
        return True

    if overdue_days <= 2:
        return False

    if 3 <= overdue_days <= 7:
        return now >= last_sent_at + timedelta(days=3)

    if 8 <= overdue_days <= 14:
        return now >= last_sent_at + timedelta(days=2)

    return now >= last_sent_at + timedelta(days=2)
