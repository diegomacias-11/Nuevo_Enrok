from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


FULL_ACCESS_GROUPS = [
    "Apoyo Comercial",
    "Dirección Operaciones",
    "Dirección Ventas",
]

BUSINESS_APP_LABELS = [
    "alianzas",
    "clientes",
    "comercial",
    "dispersiones",
    "comisiones",
]

VENTAS_GROUP = "Ventas"
VENTAS_MODEL = "comercial.Cita"
VENTAS_ACTIONS = ["view", "add", "change", "delete"]
VENTAS_VIEW_ONLY_MODELS = [
    "alianzas.Alianza",
]


class Command(BaseCommand):
    help = "Agrega permisos faltantes a los grupos de negocio sin quitar permisos existentes."

    def handle(self, *args, **options):
        business_permissions = self._business_permissions()
        ventas_permissions = list(self._model_permissions(VENTAS_MODEL, VENTAS_ACTIONS))
        for model_label in VENTAS_VIEW_ONLY_MODELS:
            ventas_permissions.extend(self._model_permissions(model_label, ["view"]))

        for group_name in FULL_ACCESS_GROUPS:
            self._add_permissions(group_name, business_permissions)

        self._add_permissions(VENTAS_GROUP, ventas_permissions)

    def _business_permissions(self):
        content_types = ContentType.objects.filter(app_label__in=BUSINESS_APP_LABELS)
        return Permission.objects.filter(content_type__in=content_types).order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        )

    def _model_permissions(self, model_label, actions):
        model = apps.get_model(model_label)
        content_type = ContentType.objects.get_for_model(model)
        codenames = [f"{action}_{model._meta.model_name}" for action in actions]
        return Permission.objects.filter(content_type=content_type, codename__in=codenames)

    def _add_permissions(self, group_name, permissions):
        group, created = Group.objects.get_or_create(name=group_name)
        existing_ids = set(group.permissions.values_list("id", flat=True))
        missing = [permission for permission in permissions if permission.id not in existing_ids]

        if missing:
            group.permissions.add(*missing)

        status = "creado" if created else "existente"
        self.stdout.write(
            self.style.SUCCESS(
                f"{group_name}: grupo {status}, {len(missing)} permisos agregados."
            )
        )
