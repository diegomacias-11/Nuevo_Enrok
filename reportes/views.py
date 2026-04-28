
from datetime import datetime, time

from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from comercial.models import Cita
from comisiones.models import Comision, PagoComision
from core.choices import (
    ESTATUS_CITA_CHOICES,
    ESTATUS_SEGUIMIENTO_CHOICES,
    POSIBILIDAD_CHOICES,
    SERVICIO_CHOICES,
)
from core.scope import can_view_reportes
from clientes.models import Cliente
from dispersiones.models import Dispersion


CHART_FILTERS = {
    "servicio": "Servicio",
    "vendedor": "Vendedor",
    "estatus_seguimiento": "Estatus seguimiento",
    "posibilidad": "Posibilidad",
    "mes": "Mes",
}

DISPERSION_CHART_FILTERS = {
    "servicio": "Servicio",
    "cliente": "Cliente",
    "estatus_pago": "Estatus pago",
}

COMISION_CHART_FILTERS = {
    "comisionista": "Comisionista",
    "cliente": "Cliente",
    "liberada": "Liberación",
    "pago_comision": "Pago comisión",
    "estatus_pago_dispersion": "Estatus pago cliente",
}

MESES_NOMBRES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def _require_reportes_access(user):
    if not can_view_reportes(user):
        raise PermissionDenied


def _choice_label_map(choices):
    return {value: label for value, label in choices}


def _date_range_filter(queryset, fecha_desde, fecha_hasta):
    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            queryset = queryset.filter(fecha_cita__gte=timezone.make_aware(datetime.combine(d, time.min), tz))
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            queryset = queryset.filter(fecha_cita__lte=timezone.make_aware(datetime.combine(d, time.max), tz))
        except ValueError:
            pass
    return queryset


def _value_counts(queryset, field, label_map=None):
    rows = (
        queryset.exclude(**{f"{field}__isnull": True})
        .exclude(**{field: ""})
        .values(field)
        .annotate(total=Count("id"))
        .order_by("-total", field)
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        value = row[field]
        values.append(str(value))
        labels.append(label_map.get(value, value) if label_map else str(value))
        totals.append(row["total"])
    return {"labels": labels, "values": values, "totals": totals}


def _value_sums(queryset, field, sum_field, label_map=None):
    rows = (
        queryset.exclude(**{f"{field}__isnull": True})
        .exclude(**{field: ""})
        .values(field)
        .annotate(total=Sum(sum_field))
        .order_by("-total", field)
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        value = row[field]
        total = row["total"] or 0
        values.append(str(value))
        labels.append(label_map.get(value, value) if label_map else str(value))
        totals.append(float(total))
    return {"labels": labels, "values": values, "totals": totals}


def _vendedor_counts(queryset):
    user_model = get_user_model()
    rows = (
        queryset.exclude(vendedor_usuario__isnull=True)
        .values("vendedor_usuario")
        .annotate(total=Count("id"))
        .order_by("-total", "vendedor_usuario")
    )
    users = user_model.objects.in_bulk([row["vendedor_usuario"] for row in rows])
    labels = []
    values = []
    totals = []
    for row in rows:
        user = users.get(row["vendedor_usuario"])
        labels.append((user.get_full_name() or user.username) if user else "Sin vendedor")
        values.append(str(row["vendedor_usuario"]))
        totals.append(row["total"])
    return {"labels": labels, "values": values, "totals": totals}


def _month_counts(queryset):
    rows = (
        queryset.annotate(mes=TruncMonth("fecha_cita"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        month = timezone.localtime(row["mes"]) if timezone.is_aware(row["mes"]) else row["mes"]
        labels.append(month.strftime("%b %Y").capitalize())
        values.append(month.strftime("%Y-%m"))
        totals.append(row["total"])
    return {"labels": labels, "values": values, "totals": totals}


def _cliente_sums(queryset):
    rows = (
        queryset.exclude(cliente__isnull=True)
        .values("cliente", "cliente__razon_social")
        .annotate(total=Sum("monto_dispersion"))
        .order_by("-total", "cliente__razon_social")
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        labels.append(row["cliente__razon_social"] or "Sin cliente")
        values.append(str(row["cliente"]))
        totals.append(float(row["total"] or 0))
    return {"labels": labels, "values": values, "totals": totals}


def _cliente_comision_sums(queryset):
    rows = (
        queryset.exclude(cliente__isnull=True)
        .values("cliente", "cliente__razon_social")
        .annotate(total=Sum("monto"))
        .order_by("-total", "cliente__razon_social")
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        labels.append(row["cliente__razon_social"] or "Sin cliente")
        values.append(str(row["cliente"]))
        totals.append(float(row["total"] or 0))
    return {"labels": labels, "values": values, "totals": totals}


def _comisionista_sums(queryset):
    rows = (
        queryset.exclude(comisionista__isnull=True)
        .values("comisionista", "comisionista__nombre")
        .annotate(total=Sum("monto"))
        .order_by("-total", "comisionista__nombre")
    )
    labels = []
    values = []
    totals = []
    for row in rows:
        labels.append(row["comisionista__nombre"] or "Sin comisionista")
        values.append(str(row["comisionista"]))
        totals.append(float(row["total"] or 0))
    return {"labels": labels, "values": values, "totals": totals}


def _boolean_sums(queryset, field, sum_field, true_label, false_label):
    rows = queryset.values(field).annotate(total=Sum(sum_field)).order_by(field)
    labels = []
    values = []
    totals = []
    for row in rows:
        value = bool(row[field])
        labels.append(true_label if value else false_label)
        values.append("True" if value else "False")
        totals.append(float(row["total"] or 0))
    return {"labels": labels, "values": values, "totals": totals}


def _coerce_mes_anio_params(request):
    today = timezone.localdate()
    mes = request.GET.get("mes") or str(today.month)
    anio = request.GET.get("anio") or str(today.year)
    if mes == "todos":
        mes_i = "todos"
    else:
        try:
            mes_i = int(mes)
            if mes_i < 1 or mes_i > 12:
                mes_i = today.month
        except (TypeError, ValueError):
            mes_i = today.month
    try:
        anio_i = int(anio)
    except (TypeError, ValueError):
        anio_i = today.year
    return mes_i, anio_i


def _apply_citas_dashboard_filters(request, queryset):
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""
    alianza = request.GET.get("alianza") or ""
    servicio = request.GET.get("servicio") or ""
    vendedor = request.GET.get("vendedor") or ""
    estatus_cita = request.GET.get("estatus_cita") or ""
    estatus_seguimiento = request.GET.get("estatus_seguimiento") or ""
    posibilidad = request.GET.get("posibilidad") or ""
    mes = request.GET.get("mes") or ""

    queryset = _date_range_filter(queryset, fecha_desde, fecha_hasta)
    if alianza:
        queryset = queryset.filter(alianza=alianza == "True")
    if servicio:
        queryset = queryset.filter(servicio=servicio)
    if vendedor:
        queryset = queryset.filter(vendedor_usuario_id=vendedor)
    if estatus_cita:
        queryset = queryset.filter(estatus_cita=estatus_cita)
    if estatus_seguimiento:
        queryset = queryset.filter(estatus_seguimiento=estatus_seguimiento)
    if posibilidad:
        queryset = queryset.filter(posibilidad=posibilidad)
    if mes:
        try:
            year, month = [int(part) for part in mes.split("-", 1)]
            queryset = queryset.filter(fecha_cita__year=year, fecha_cita__month=month)
        except ValueError:
            pass

    return queryset, {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "alianza": alianza,
        "servicio": servicio,
        "vendedor": vendedor,
        "estatus_cita": estatus_cita,
        "estatus_seguimiento": estatus_seguimiento,
        "posibilidad": posibilidad,
        "mes": mes,
    }


def _active_citas_filters(params, chart_data):
    labels_by_field = {
        "servicio": dict(zip(chart_data["servicio"]["values"], chart_data["servicio"]["labels"])),
        "vendedor": dict(zip(chart_data["vendedor"]["values"], chart_data["vendedor"]["labels"])),
        "estatus_seguimiento": dict(
            zip(chart_data["estatus_seguimiento"]["values"], chart_data["estatus_seguimiento"]["labels"])
        ),
        "posibilidad": dict(zip(chart_data["posibilidad"]["values"], chart_data["posibilidad"]["labels"])),
        "mes": dict(zip(chart_data["mes"]["values"], chart_data["mes"]["labels"])),
    }
    active = []
    for field, title in CHART_FILTERS.items():
        value = params.get(field)
        if value:
            active.append(
                {
                    "field": field,
                    "title": title,
                    "value": labels_by_field.get(field, {}).get(value, value),
                }
            )
    return active


def _apply_dispersiones_dashboard_filters(request, queryset):
    mes, anio = _coerce_mes_anio_params(request)
    servicio = request.GET.get("servicio") or ""
    cliente = request.GET.get("cliente") or ""
    estatus_pago = request.GET.get("estatus_pago") or ""

    queryset = queryset.filter(fecha__year=anio)
    if mes != "todos":
        queryset = queryset.filter(fecha__month=mes)
    if servicio:
        queryset = queryset.filter(servicio=servicio)
    if cliente:
        queryset = queryset.filter(cliente_id=cliente)
    if estatus_pago:
        queryset = queryset.filter(estatus_pago=estatus_pago)

    return queryset, {
        "mes": str(mes),
        "anio": str(anio),
        "servicio": servicio,
        "cliente": cliente,
        "estatus_pago": estatus_pago,
    }


def _active_dispersion_filters(params, chart_data):
    labels_by_field = {
        "servicio": dict(zip(chart_data["servicio"]["values"], chart_data["servicio"]["labels"])),
        "cliente": dict(zip(chart_data["cliente"]["values"], chart_data["cliente"]["labels"])),
        "estatus_pago": dict(zip(chart_data["estatus_pago"]["values"], chart_data["estatus_pago"]["labels"])),
    }
    active = []
    for field, title in DISPERSION_CHART_FILTERS.items():
        value = params.get(field)
        if value:
            active.append(
                {
                    "field": field,
                    "title": title,
                    "value": labels_by_field.get(field, {}).get(value, value),
                }
            )
    return active


def _apply_comisiones_dashboard_filters(request, queryset):
    mes, anio = _coerce_mes_anio_params(request)
    comisionista = request.GET.get("comisionista") or ""
    cliente = request.GET.get("cliente") or ""
    liberada = request.GET.get("liberada") or ""
    pago_comision = request.GET.get("pago_comision") or ""
    estatus_pago_dispersion = request.GET.get("estatus_pago_dispersion") or ""

    queryset = queryset.filter(periodo_anio=anio)
    if mes != "todos":
        queryset = queryset.filter(periodo_mes=mes)
    if comisionista:
        queryset = queryset.filter(comisionista_id=comisionista)
    if cliente:
        queryset = queryset.filter(cliente_id=cliente)
    if liberada:
        queryset = queryset.filter(liberada=liberada == "True")
    if pago_comision:
        queryset = queryset.filter(pago_comision=pago_comision == "True")
    if estatus_pago_dispersion:
        queryset = queryset.filter(estatus_pago_dispersion=estatus_pago_dispersion)

    return queryset, {
        "mes": str(mes),
        "anio": str(anio),
        "comisionista": comisionista,
        "cliente": cliente,
        "liberada": liberada,
        "pago_comision": pago_comision,
        "estatus_pago_dispersion": estatus_pago_dispersion,
    }


def _comisiones_payment_queryset(params):
    pagos = PagoComision.objects.filter(periodo_anio=params["anio"])
    if params["mes"] != "todos":
        pagos = pagos.filter(periodo_mes=params["mes"])
    if params["comisionista"]:
        pagos = pagos.filter(comisionista_id=params["comisionista"])
    if params["cliente"]:
        pagos = pagos.filter(comision__cliente_id=params["cliente"])
    if params["liberada"]:
        pagos = pagos.filter(comision__liberada=params["liberada"] == "True")
    if params["pago_comision"]:
        pagos = pagos.filter(comision__pago_comision=params["pago_comision"] == "True")
    if params["estatus_pago_dispersion"]:
        pagos = pagos.filter(comision__estatus_pago_dispersion=params["estatus_pago_dispersion"])
    return pagos


def _generated_vs_paid_by_comisionista(comisiones, pagos):
    generated_rows = (
        comisiones.exclude(comisionista__isnull=True)
        .values("comisionista", "comisionista__nombre")
        .annotate(total=Sum("monto"))
        .order_by("-total", "comisionista__nombre")
    )
    paid_rows = pagos.values("comisionista").annotate(total=Sum("monto"))
    paid_map = {str(row["comisionista"]): float(row["total"] or 0) for row in paid_rows}

    labels = []
    values = []
    generated = []
    paid = []
    for row in generated_rows:
        key = str(row["comisionista"])
        labels.append(row["comisionista__nombre"] or "Sin comisionista")
        values.append(key)
        generated.append(float(row["total"] or 0))
        paid.append(paid_map.get(key, 0))

    return {"labels": labels, "values": values, "generated": generated, "paid": paid}


def _active_comision_filters(params, chart_data):
    labels_by_field = {
        "comisionista": dict(zip(chart_data["comisionista"]["values"], chart_data["comisionista"]["labels"])),
        "cliente": dict(zip(chart_data["cliente"]["values"], chart_data["cliente"]["labels"])),
        "liberada": dict(zip(chart_data["liberada"]["values"], chart_data["liberada"]["labels"])),
        "pago_comision": dict(zip(chart_data["pago_comision"]["values"], chart_data["pago_comision"]["labels"])),
        "estatus_pago_dispersion": dict(
            zip(chart_data["estatus_pago_dispersion"]["values"], chart_data["estatus_pago_dispersion"]["labels"])
        ),
    }
    active = []
    for field, title in COMISION_CHART_FILTERS.items():
        value = params.get(field)
        if value:
            active.append(
                {
                    "field": field,
                    "title": title,
                    "value": labels_by_field.get(field, {}).get(value, value),
                }
            )
    return active


def reporte_looker(request):
    """Renderiza el dashboard de Looker Studio embebido."""
    _require_reportes_access(request.user)
    return render(request, 'reportes/looker.html')


def reportes_home(request):
    _require_reportes_access(request.user)
    return render(request, "reportes/dashboard_nav.html")


def dashboard_citas(request):
    _require_reportes_access(request.user)
    citas, params = _apply_citas_dashboard_filters(request, Cita.objects.all())
    chart_data = {
        "servicio": _value_counts(citas, "servicio", _choice_label_map(SERVICIO_CHOICES)),
        "vendedor": _vendedor_counts(citas),
        "estatus_seguimiento": _value_counts(
            citas,
            "estatus_seguimiento",
            _choice_label_map(ESTATUS_SEGUIMIENTO_CHOICES),
        ),
        "posibilidad": _value_counts(citas, "posibilidad", _choice_label_map(POSIBILIDAD_CHOICES)),
        "mes": _month_counts(citas),
    }
    context = {
        "dashboard_active": "citas",
        "fecha_desde": params["fecha_desde"],
        "fecha_hasta": params["fecha_hasta"],
        "alianza": params["alianza"],
        "estatus_cita": params["estatus_cita"],
        "estatus_cita_choices": ESTATUS_CITA_CHOICES,
        "chart_filters": {field: params[field] for field in CHART_FILTERS},
        "active_chart_filters": _active_citas_filters(params, chart_data),
        "total_citas": citas.count(),
        "chart_data": chart_data,
    }
    return render(request, "reportes/dashboard_citas.html", context)


def dashboard_dispersiones(request):
    _require_reportes_access(request.user)
    dispersiones, params = _apply_dispersiones_dashboard_filters(request, Dispersion.objects.select_related("cliente"))
    chart_data = {
        "servicio": _value_sums(dispersiones, "servicio", "monto_dispersion"),
        "cliente": _cliente_sums(dispersiones),
        "estatus_pago": _value_sums(
            dispersiones,
            "estatus_pago",
            "monto_dispersion",
            _choice_label_map(Dispersion.EstatusPago.choices),
        ),
    }
    context = {
        "dashboard_active": "dispersiones",
        "mes": params["mes"],
        "anio": params["anio"],
        "mes_nombre": "Todos los meses" if params["mes"] == "todos" else MESES_NOMBRES[int(params["mes"])],
        "meses_choices": [(i, MESES_NOMBRES[i]) for i in range(1, 13)],
        "chart_filters": {field: params[field] for field in DISPERSION_CHART_FILTERS},
        "active_chart_filters": _active_dispersion_filters(params, chart_data),
        "total_dispersiones": dispersiones.count(),
        "total_monto_dispersion": dispersiones.aggregate(total=Sum("monto_dispersion"))["total"] or 0,
        "total_monto_comision": dispersiones.aggregate(total=Sum("monto_comision"))["total"] or 0,
        "chart_data": chart_data,
    }
    return render(request, "reportes/dashboard_dispersiones.html", context)


def dashboard_comisiones(request):
    _require_reportes_access(request.user)
    comisiones, params = _apply_comisiones_dashboard_filters(
        request,
        Comision.objects.select_related("cliente", "comisionista", "dispersion"),
    )
    pagos = _comisiones_payment_queryset(params)
    chart_data = {
        "comisionista": _comisionista_sums(comisiones),
        "liberada": _boolean_sums(comisiones, "liberada", "monto", "Liberado", "No liberado"),
        "pago_comision": _boolean_sums(comisiones, "pago_comision", "monto", "Pagado", "No pagado"),
        "cliente": _cliente_comision_sums(comisiones),
        "estatus_pago_dispersion": _value_sums(comisiones, "estatus_pago_dispersion", "monto"),
        "generado_pagado": _generated_vs_paid_by_comisionista(comisiones, pagos),
    }
    total_periodo = comisiones.aggregate(total=Sum("monto"))["total"] or 0
    total_liberado = comisiones.filter(liberada=True).aggregate(total=Sum("monto"))["total"] or 0
    total_pagos = pagos.aggregate(total=Sum("monto"))["total"] or 0
    context = {
        "dashboard_active": "comisiones",
        "mes": params["mes"],
        "anio": params["anio"],
        "mes_nombre": "Todos los meses" if params["mes"] == "todos" else MESES_NOMBRES[int(params["mes"])],
        "meses_choices": [(i, MESES_NOMBRES[i]) for i in range(1, 13)],
        "clientes": Cliente.objects.order_by("razon_social"),
        "cliente_id": params["cliente"],
        "chart_filters": {field: params[field] for field in COMISION_CHART_FILTERS},
        "active_chart_filters": _active_comision_filters(params, chart_data),
        "total_comisiones": comisiones.count(),
        "total_periodo": total_periodo,
        "total_liberado": total_liberado,
        "total_pagos": total_pagos,
        "total_pendiente": total_liberado - total_pagos,
        "chart_data": chart_data,
    }
    return render(request, "reportes/dashboard_comisiones.html", context)
