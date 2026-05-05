from importlib import import_module

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.template.loader import select_template

from core.config_areas import get_project_models


def get_reportable_models():
    return get_project_models()


def get_reportable_model_key(model) -> str:
    return model._meta.label


def get_reportable_model_label(model) -> str:
    return model._meta.verbose_name_plural.title()


def get_reportable_model_choices():
    return [
        (get_reportable_model_key(model), get_reportable_model_label(model))
        for model in get_reportable_models()
    ]


def get_reportable_model_by_key(key: str):
    normalized_key = (key or "").strip().lower()
    for model in get_reportable_models():
        if get_reportable_model_key(model).lower() == normalized_key:
            return model
    raise ImproperlyConfigured(f"Modelo reportable no registrado: {key}")


def get_reportable_field_label(model, field_name: str) -> str:
    try:
        return model._meta.get_field(field_name).verbose_name.title()
    except FieldDoesNotExist:
        return field_name.replace("_", " ").title()


def get_reportable_field_choices(model):
    fields = []
    numeric_types = (
        "IntegerField", "FloatField", "DecimalField", "BigIntegerField",
        "PositiveIntegerField", "SmallIntegerField", "PositiveSmallIntegerField"
    )
    for field in model._meta.fields:
        if not getattr(field, "editable", True) and field.name != "id":
            continue
        is_numeric = field.get_internal_type() in numeric_types
        fields.append(
            {
                "name": field.name,
                "label": get_reportable_field_label(model, field.name),
                "is_numeric": is_numeric,
            }
        )
    return fields


def get_report_filters_template(model) -> str:
    app_label = model._meta.app_label
    candidates = [
        f"{app_label}/partials/{model._meta.model_name}_filtros_lista.html",
        f"{app_label}/partials/filtros_lista.html",
    ]
    for template_name in candidates:
        try:
            select_template([template_name])
            return template_name
        except Exception:
            continue
    return candidates[-1]


def get_report_adapter(model):
    try:
        return import_module(f"{model._meta.app_label}.reporting")
    except ModuleNotFoundError as exc:
        if exc.name == f"{model._meta.app_label}.reporting":
            return None
        raise
