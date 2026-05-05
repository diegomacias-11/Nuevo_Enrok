from pathlib import Path

from django.apps import apps
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SKIP_MODELS = {ContentType, Session, LogEntry}
_SKIP_LABELS = {"auth.permission", "admin.logentry"}


def _is_project_app(app_config) -> bool:
    try:
        app_path = Path(app_config.path).resolve()
    except Exception:
        return False
    return app_path == _PROJECT_ROOT or _PROJECT_ROOT in app_path.parents


def get_project_models():
    project_labels = {
        app_config.label
        for app_config in apps.get_app_configs()
        if _is_project_app(app_config)
    }
    models = []
    for model in apps.get_models():
        meta = model._meta
        if meta.app_label not in project_labels:
            continue
        if model in _SKIP_MODELS or meta.label_lower in _SKIP_LABELS:
            continue
        if meta.auto_created or meta.proxy:
            continue
        if not meta.managed:
            continue
        models.append(model)
    return sorted(models, key=lambda model: (model._meta.app_label, model._meta.model_name))
