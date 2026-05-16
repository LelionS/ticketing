from django.urls import path
from . import views

urlpatterns = [
    path(
        "ticket/<int:ticket_id>/file/<int:file_id>/",
        views.download_ticket_file,
        name="download_ticket_file",
    ),
]
