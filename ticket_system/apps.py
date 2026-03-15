from django.apps import AppConfig


class TicketSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ticket_system'

    def ready(self):
        import ticket_system.signals  # ensures signals update TicketReport automatically