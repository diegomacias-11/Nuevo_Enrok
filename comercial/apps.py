from django.apps import AppConfig


class ComercialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comercial"

    def ready(self):
        # Import signals lazily; ignore failures during migrations/startup
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
