from .scope import can_view_reportes


def navigation_scope(request):
    return {
        "can_view_reportes": can_view_reportes(request.user),
    }
