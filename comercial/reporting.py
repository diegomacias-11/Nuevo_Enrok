from .views import _cita_filter_context, _filtered_citas


def get_field_choices(_model):
    return [
        {"name": "id", "label": "Id", "is_numeric": True},
        {"name": "prospecto", "label": "Prospecto", "is_numeric": False},
        {"name": "alianza", "label": "Alianza", "is_numeric": False},
        {"name": "giro", "label": "Giro", "is_numeric": False},
        {"name": "tipo", "label": "Tipo", "is_numeric": False},
        {"name": "medio", "label": "Medio", "is_numeric": False},
        {"name": "servicio", "label": "Servicio", "is_numeric": False},
        {"name": "servicio2", "label": "Servicio 2", "is_numeric": False},
        {"name": "servicio3", "label": "Servicio 3", "is_numeric": False},
        {"name": "contacto", "label": "Contacto", "is_numeric": False},
        {"name": "telefono", "label": "Telefono", "is_numeric": False},
        {"name": "correo", "label": "Correo", "is_numeric": False},
        {"name": "conexion", "label": "Conexion", "is_numeric": False},
        {"name": "vendedor_display", "label": "Vendedor", "is_numeric": False},
        {"name": "estatus_cita", "label": "Estatus Cita", "is_numeric": False},
        {"name": "numero_cita", "label": "Numero Cita", "is_numeric": False},
        {"name": "estatus_seguimiento", "label": "Estatus Seguimiento", "is_numeric": False},
        {"name": "posibilidad", "label": "Posibilidad", "is_numeric": False},
        {"name": "comentarios", "label": "Comentarios", "is_numeric": False},
        {"name": "lugar", "label": "Lugar", "is_numeric": False},
        {"name": "fecha_cita", "label": "Fecha Cita", "is_numeric": False},
        {"name": "fecha_registro", "label": "Fecha Registro", "is_numeric": False},
    ]


def get_filter_context(request):
    return _cita_filter_context(request)


def get_queryset(request):
    citas, _context = _filtered_citas(request)
    return citas
