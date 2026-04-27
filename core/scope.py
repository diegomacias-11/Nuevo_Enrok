from dataclasses import replace

from django.core.exceptions import PermissionDenied


VENTAS_GROUP = "Ventas"


def user_in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_ventas_user(user):
    return user_in_group(user, VENTAS_GROUP)


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
