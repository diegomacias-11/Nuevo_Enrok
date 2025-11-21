from django.apps import AppConfig


class ComisionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comisiones'

    def ready(self):
        # Import signals on app ready
        from . import signals  # noqa: F401

