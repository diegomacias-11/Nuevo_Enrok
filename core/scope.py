from dataclasses import replace

from django.core.exceptions import PermissionDenied


REPORTE_CITAS = "citas"
REPORTE_DISPERSIONES = "dispersiones"
REPORTE_COMISIONES = "comisiones"

REPORTES_SCOPE_BY_GROUP = {
    "Ventas": {REPORTE_CITAS},
    "Apoyo Comercial": {REPORTE_CITAS, REPORTE_DISPERSIONES, REPORTE_COMISIONES},
    "Dirección Operaciones": {REPORTE_CITAS, REPORTE_DISPERSIONES, REPORTE_COMISIONES},
    "Dirección Ventas": {REPORTE_CITAS, REPORTE_DISPERSIONES, REPORTE_COMISIONES},
}


def user_in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_ventas_user(user):
    return user_in_group(user, "Ventas")


def can_view_reportes(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm("reportes.view_reporte")


def can_view_reporte(user, reporte):
    if not can_view_reportes(user):
        return False
    if user.is_superuser:
        return True

    allowed_groups = [
        group_name
        for group_name, reportes in REPORTES_SCOPE_BY_GROUP.items()
        if reporte in reportes
    ]
    return user.groups.filter(name__in=allowed_groups).exists()


def reportes_permitidos(user):
    return {
        reporte
        for reportes in REPORTES_SCOPE_BY_GROUP.values()
        for reporte in reportes
        if can_view_reporte(user, reporte)
    }


def can_change_cita(user, cita, access):
    if not access.can_change:
        return False
    if is_ventas_user(user):
        return cita.vendedor_usuario_id == user.id
    return True


def can_delete_cita(user, cita, access):
    if not access.can_delete:
        return False
    if is_ventas_user(user):
        return cita.vendedor_usuario_id == user.id
    return True


def scoped_cita_access(user, cita, access):
    return replace(
        access,
        can_change=can_change_cita(user, cita, access),
        can_delete=can_delete_cita(user, cita, access),
    )


def require_cita_change_scope(user, cita, access):
    if not can_change_cita(user, cita, access):
        raise PermissionDenied


def require_cita_delete_scope(user, cita, access):
    if not can_delete_cita(user, cita, access):
        raise PermissionDenied
