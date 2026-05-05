from .views import _cita_filter_context, _filtered_citas


def get_filter_context(request):
    return _cita_filter_context(request)


def get_queryset(request):
    citas, _context = _filtered_citas(request)
    return citas
