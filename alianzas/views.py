from datetime import datetime, time

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.access import (
    access_context,
    disable_form_fields,
    get_model_access,
    require_form_access,
    require_model_permission,
)

from .models import Alianza
from .forms import AlianzaForm


def alianzas_lista(request):
    access = get_model_access(request.user, Alianza)
    require_model_permission(request.user, Alianza, "view")

    q = (request.GET.get("q") or "").strip()
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

    alianzas_qs = Alianza.objects.all()
    if q:
        alianzas_qs = alianzas_qs.filter(nombre__icontains=q)

    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            alianzas_qs = alianzas_qs.filter(fecha_registro__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            alianzas_qs = alianzas_qs.filter(fecha_registro__lte=end_dt)
        except ValueError:
            pass

    alianzas = alianzas_qs.order_by("-fecha_registro")

    context = {
        "alianzas": alianzas,
        "q": q,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    context.update(access_context(access))
    return render(request, "alianzas/lista.html", context)


def agregar_alianza(request):
    access = get_model_access(request.user, Alianza)
    require_model_permission(request.user, Alianza, "add")
    back_url = request.GET.get("next") or reverse("alianzas_lista")

    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = AlianzaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = AlianzaForm()

    context = {
        "form": form,
        "back_url": back_url,
    }
    context.update(access_context(access))
    return render(request, "alianzas/form.html", context)


def editar_alianza(request, id: int):
    access = require_form_access(request.user, Alianza)
    alianza = get_object_or_404(Alianza, pk=id)
    back_url = request.GET.get("next") or reverse("alianzas_lista")

    if request.method == "POST":
        require_model_permission(request.user, Alianza, "change")
        back_url = request.POST.get("next") or back_url
        form = AlianzaForm(request.POST, instance=alianza)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = AlianzaForm(instance=alianza)
        if access.read_only:
            disable_form_fields(form)

    context = {
        "form": form,
        "alianza": alianza,
        "back_url": back_url,
    }
    context.update(access_context(access))
    return render(request, "alianzas/form.html", context)


def eliminar_alianza(request, id: int):
    require_model_permission(request.user, Alianza, "delete")
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("alianzas_lista")
    alianza = get_object_or_404(Alianza, pk=id)
    alianza.delete()
    return redirect(back_url)
