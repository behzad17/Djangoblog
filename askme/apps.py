from django.apps import AppConfig


class AskmeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'askme'
    
    def ready(self):
        """Import signals when app is ready."""
        import askme.signals  # noqa