from dataclasses import dataclass

from django.core.exceptions import PermissionDenied


@dataclass(frozen=True)
class ModelAccess:
    can_view: bool
    can_add: bool
    can_change: bool
    can_delete: bool

    @property
    def can_access_form(self):
        return self.can_view or self.can_change

    @property
    def read_only(self):
        return self.can_view and not self.can_change


def permission_codename(model, action):
    opts = model._meta
    return f"{opts.app_label}.{action}_{opts.model_name}"


def get_model_access(user, model):
    return ModelAccess(
        can_view=user.has_perm(permission_codename(model, "view")),
        can_add=user.has_perm(permission_codename(model, "add")),
        can_change=user.has_perm(permission_codename(model, "change")),
        can_delete=user.has_perm(permission_codename(model, "delete")),
    )


def require_model_permission(user, model, action):
    if not user.has_perm(permission_codename(model, action)):
        raise PermissionDenied


def require_form_access(user, model):
    access = get_model_access(user, model)
    if not access.can_access_form:
        raise PermissionDenied
    return access


def disable_form_fields(form):
    for field in form.fields.values():
        field.disabled = True
    return form


def access_context(access):
    return {
        "access": access,
        "can_view": access.can_view,
        "can_add": access.can_add,
        "can_change": access.can_change,
        "can_delete": access.can_delete,
        "read_only": access.read_only,
    }
