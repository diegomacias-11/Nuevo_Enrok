from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from core.access import (
    access_context,
    disable_form_fields,
    get_model_access,
    require_form_access,
    require_model_permission,
)
from .models import Dispersion
from .forms import DispersionForm


def _coerce_mes_anio(request):
    now = datetime.now()
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    if not mes or not anio:
        # Redirect preserving other query params
        return None, None, redirect(f"{request.path}?mes={now.month}&anio={now.year}")
    try:
        mes_i = int(mes)
        if mes_i < 1 or mes_i > 12:
            mes_i = now.month
    except (TypeError, ValueError):
        mes_i = now.month
    try:
        anio_i = int(anio)
    except (TypeError, ValueError):
        anio_i = now.year
    return mes_i, anio_i, None


def dispersiones_lista(request):
    access = get_model_access(request.user, Dispersion)
    require_model_permission(request.user, Dispersion, "view")

    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir

    dispersiones = Dispersion.objects.filter(fecha__month=mes, fecha__year=anio).order_by("fecha")

    # Nombre de mes en español
    meses_nombres = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    meses_choices = [(i, meses_nombres[i]) for i in range(1, 13)]
    context = {
        "dispersiones": dispersiones,
        "mes": str(mes),
        "anio": str(anio),
        "meses": list(range(1, 13)),
        "meses_choices": meses_choices,
        "mes_nombre": meses_nombres[mes],
    }
    context.update(access_context(access))
    return render(request, "dispersiones/lista.html", context)


def agregar_dispersion(request):
    access = get_model_access(request.user, Dispersion)
    require_model_permission(request.user, Dispersion, "add")

    mes, anio, redir = _coerce_mes_anio(request)
    if redir and request.method != "POST":
        return redir
    back_url = request.GET.get("next") or f"{reverse('dispersiones_lista')}?mes={mes}&anio={anio}"

    if request.method == "POST":
        mes = int(request.POST.get("mes") or mes or datetime.now().month)
        anio = int(request.POST.get("anio") or anio or datetime.now().year)
        form = DispersionForm(request.POST, mes=mes, anio=anio)
        if form.is_valid():
            disp = form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = DispersionForm(mes=mes, anio=anio)
    context = {"form": form, "back_url": back_url, "mes": mes, "anio": anio}
    context.update(access_context(access))
    return render(request, "dispersiones/form.html", context)


def editar_dispersion(request, id: int):
    access = require_form_access(request.user, Dispersion)
    disp = get_object_or_404(Dispersion, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = request.GET.get("next") or f"{reverse('dispersiones_lista')}?mes={mes}&anio={anio}"
    if request.method == "POST":
        require_model_permission(request.user, Dispersion, "change")
        form = DispersionForm(request.POST, instance=disp, mes=mes, anio=anio)
        if form.is_valid():
            form.save()
            return redirect(request.POST.get("next") or back_url)
    else:
        form = DispersionForm(instance=disp, mes=mes, anio=anio)
        if access.read_only:
            disable_form_fields(form)
    context = {"form": form, "dispersion": disp, "back_url": back_url, "mes": mes, "anio": anio}
    context.update(access_context(access))
    return render(request, "dispersiones/form.html", context)


def eliminar_dispersion(request, id: int):
    require_model_permission(request.user, Dispersion, "delete")
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("dispersiones_lista")
    disp = get_object_or_404(Dispersion, pk=id)
    disp.delete()
    return redirect(back_url)
