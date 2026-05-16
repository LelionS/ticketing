from django.shortcuts import render

# Create your views here.
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .models import TicketAttachment


def download_ticket_file(request, ticket_id, file_id):
    attachment = get_object_or_404(
        TicketAttachment,
        id=file_id,
        ticket_id=ticket_id
    )

    if not attachment.file:
        raise Http404("File not found")

    return FileResponse(
        attachment.file.open("rb"),
        as_attachment=True,
        filename=attachment.filename()
    )
