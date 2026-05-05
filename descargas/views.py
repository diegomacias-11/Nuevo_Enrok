from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template.loader import select_template
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.safestring import mark_safe
import json

from .registry import (
    get_report_adapter,
    get_reportable_field_choices,
    get_reportable_model_by_key,
    get_reportable_model_label,
    get_report_filters_template,
)
from .services import build_excel_report, build_pdf_report


def _format_preview_value(value):
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return date_format(value, "d/m/Y")
    return str(value)


def _build_preview_rows(rows, fields, limit=5):
    preview_rows = []
    field_names = [field["name"] for field in fields]
    for row in list(rows)[:limit]:
        preview_rows.append(
            {
                field_name: _format_preview_value(getattr(row, field_name, ""))
                for field_name in field_names
            }
        )
    return preview_rows


def construir_reporte(request):
    source = (request.GET.get("source") or request.POST.get("source") or "").strip()
    if not source:
        raise Http404

    model = get_reportable_model_by_key(source)
    perm = f"{model._meta.app_label}.view_{model._meta.model_name}"
    if not request.user.is_superuser and not request.user.has_perm(perm):
        raise PermissionDenied

    adapter = get_report_adapter(model)
    fields = get_reportable_field_choices(model)
    if request.method == "POST":
        request.GET = request.POST.copy()
        rows = adapter.get_queryset(request) if adapter and hasattr(adapter, "get_queryset") else []
        if request.POST.get("archivo") == "excel":
            excel, filename = build_excel_report(rows, fields, request.POST)
            response = HttpResponse(
                excel,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            pdf, filename = build_pdf_report(rows, fields, request.POST)
            response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    filters_template = get_report_filters_template(model)
    try:
        select_template([filters_template])
    except Exception:
        filters_template = ""
    config_field_names = {
        "archivo",
        "columnas",
        "columnas_orden",
        "columnas_totales",
        "pdf_bloque_titulo",
        "pdf_titulo",
        "pdf_bloque_fecha",
        "pdf_fecha",
        "pdf_bloque_subtitulo",
        "pdf_subtitulo",
        "pdf_bloque_parrafo",
        "pdf_parrafo",
        "pdf_bloque_tabla",
        "pdf_bloque_pie",
        "pdf_pie",
        "excel_titulo_archivo",
        "excel_incluir_fecha_archivo",
        "excel_fecha_archivo",
        "excel_incluir_encabezados",
        "excel_incluir_conteo",
    }

    context = {
        "source": source,
        "model_label": get_reportable_model_label(model),
        "fields": fields,
        "filters_template": filters_template,
        "clean_url": f"{request.path}?source={source}",
        "result_count": None,
        "preview_rows_json": mark_safe("[]"),
        "today_iso": timezone.localdate().isoformat(),
        "config_query": request.GET,
        "config_has_params": bool(request.GET),
        "selected_columns_config": request.GET.getlist("columnas"),
        "selected_total_columns_config": request.GET.getlist("columnas_totales"),
        "filter_hidden_fields": [
            {"name": key, "value": value}
            for key, values in request.GET.lists()
            for value in values
            if key not in {"source", "next"} and key not in config_field_names
        ],
    }
    if adapter and hasattr(adapter, "get_filter_context"):
        context.update(adapter.get_filter_context(request))
    if adapter and hasattr(adapter, "get_queryset"):
        rows = adapter.get_queryset(request)
        context["result_count"] = len(rows)
        context["preview_rows_json"] = mark_safe(json.dumps(_build_preview_rows(rows, fields), ensure_ascii=False))

    return render(
        request,
        "descargas/constructor.html",
        context,
    )
