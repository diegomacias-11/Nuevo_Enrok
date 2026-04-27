from datetime import datetime, time

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.choices import ESTATUS_SEGUIMIENTO_CHOICES
from core.access import (
    access_context,
    disable_form_fields,
    get_model_access,
    require_form_access,
    require_model_permission,
)
from core.scope import require_cita_change_scope, require_cita_delete_scope, scoped_cita_access

from .forms import CitaForm
from .models import Cita, NUM_CITA_CHOICES


NUMERO_CITA_ORDER = [choice for choice, _ in NUM_CITA_CHOICES]


def _siguiente_numero_cita(actual: str | None) -> str | None:
    """
    Devuelve el valor siguiente de numero_cita respetando el orden de NUM_CITA_CHOICES.
    Si no hay siguiente o no coincide con la lista, se regresa el valor original.
    """
    if actual in NUMERO_CITA_ORDER:
        idx = NUMERO_CITA_ORDER.index(actual)
        if idx + 1 < len(NUMERO_CITA_ORDER):
            return NUMERO_CITA_ORDER[idx + 1]
    return actual


def _initial_desde_cita(cita: Cita) -> dict:
    """Construye los valores iniciales para registrar una nueva cita tomando otra como base."""
    return {
        "prospecto": cita.prospecto,
        "giro": cita.giro,
        "tipo": cita.tipo,
        "servicio": cita.servicio,
        "servicio2": cita.servicio2,
        "servicio3": cita.servicio3,
        "contacto": cita.contacto,
        "telefono": cita.telefono,
        "correo": cita.correo,
        "conexion": cita.conexion,
        "medio": cita.medio,
        "estatus_cita": cita.estatus_cita,
        "numero_cita": _siguiente_numero_cita(cita.numero_cita),
        "lugar": cita.lugar,
        "estatus_seguimiento": cita.estatus_seguimiento,
        "comentarios": cita.comentarios,
        "vendedor_usuario": cita.vendedor_usuario,
    }


def citas_lista(request: HttpRequest) -> HttpResponse:
    access = get_model_access(request.user, Cita)
    require_model_permission(request.user, Cita, "view")

    citas = Cita.objects.all().order_by("-fecha_registro")
    prospecto = (request.GET.get("prospecto") or "").strip()
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""
    estatus_seguimiento = request.GET.get("estatus_seguimiento") or ""
    vendedor = request.GET.get("vendedor") or ""

    if prospecto:
        citas = citas.filter(prospecto__icontains=prospecto)
    if vendedor:
        citas = citas.filter(vendedor_usuario__icontains=vendedor)

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            citas = citas.filter(fecha_cita__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            citas = citas.filter(fecha_cita__lte=end_dt)
        except ValueError:
            pass
    if estatus_seguimiento:
        citas = citas.filter(estatus_seguimiento=estatus_seguimiento)
    context = {
        "citas": citas,
        "prospecto": prospecto,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "estatus_seguimiento": estatus_seguimiento,
        "estatus_seguimiento_choices": ESTATUS_SEGUIMIENTO_CHOICES,
        "vendedor": vendedor,
    }
    context.update(access_context(access))
    return render(request, "comercial/lista.html", context)


def agregar_cita(request: HttpRequest) -> HttpResponse:
    access = get_model_access(request.user, Cita)
    require_model_permission(request.user, Cita, "add")

    back_url = request.GET.get("next") or reverse("citas_lista")
    copy_from = request.GET.get("copy_from")
    initial_data = {}
    if copy_from:
        origen = get_object_or_404(Cita, pk=copy_from)
        initial_data = _initial_desde_cita(origen)
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = CitaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm(initial=initial_data)

    context = {"form": form, "back_url": back_url}
    context.update(access_context(access))
    return render(request, "comercial/form.html", context)


def editar_cita(request: HttpRequest, id: int) -> HttpResponse:
    access = require_form_access(request.user, Cita)
    back_url = request.GET.get("next") or reverse("citas_lista")
    cita = get_object_or_404(Cita, pk=id)
    access = scoped_cita_access(request.user, cita, access)
    if request.method == "POST":
        require_model_permission(request.user, Cita, "change")
        require_cita_change_scope(request.user, cita, access)
        back_url = request.POST.get("next") or back_url
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = CitaForm(instance=cita)
        if not access.can_change:
            disable_form_fields(form)

    context = {"form": form, "back_url": back_url}
    context.update(access_context(access))
    return render(request, "comercial/form.html", context)


def eliminar_cita(request: HttpRequest, id: int) -> HttpResponse:
    require_model_permission(request.user, Cita, "delete")
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("citas_lista")
    cita = get_object_or_404(Cita, pk=id)
    access = get_model_access(request.user, Cita)
    require_cita_delete_scope(request.user, cita, access)
    cita.delete()
    return redirect(back_url)
