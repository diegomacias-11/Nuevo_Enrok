from datetime import datetime, time

from django.db.models import Q
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
from core.choices import SERVICIO_CHOICES

from .models import Cliente
from .forms import ClienteForm


def clientes_lista(request):
    access = get_model_access(request.user, Cliente)
    require_model_permission(request.user, Cliente, "view")

    q = (request.GET.get("q") or "").strip()
    alianza = (request.GET.get("alianza") or "").strip()
    servicio = (request.GET.get("servicio") or "").strip()
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

    qs = Cliente.objects.all()
    if q:
        qs = qs.filter(razon_social__icontains=q)
    if alianza:
        alianza_filter = Q()
        for i in range(1, 11):
            alianza_filter |= Q(**{f"comisionista{i}__nombre__icontains": alianza})
        qs = qs.filter(alianza_filter).distinct()
    if servicio:
        qs = qs.filter(servicio=servicio)
    tz = timezone.get_current_timezone()
    if fecha_desde:
        try:
            d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(d, time.min), tz)
            qs = qs.filter(fecha_registro__gte=start_dt)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            d = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(d, time.max), tz)
            qs = qs.filter(fecha_registro__lte=end_dt)
        except ValueError:
            pass
    clientes = qs.order_by("-fecha_registro")

    context = {
        "clientes": clientes,
        "q": q,
        "alianza": alianza,
        "servicio": servicio,
        "servicio_choices": SERVICIO_CHOICES,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    context.update(access_context(access))
    return render(request, "clientes/lista.html", context)


def agregar_cliente(request):
    access = get_model_access(request.user, Cliente)
    require_model_permission(request.user, Cliente, "add")
    back_url = request.GET.get("next") or reverse("clientes_lista")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ClienteForm()
    context = {"form": form, "back_url": back_url}
    context.update(access_context(access))
    return render(request, "clientes/form.html", context)


def editar_cliente(request, id: int):
    access = require_form_access(request.user, Cliente)
    cliente = get_object_or_404(Cliente, pk=id)
    back_url = request.GET.get("next") or reverse("clientes_lista")
    if request.method == "POST":
        require_model_permission(request.user, Cliente, "change")
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ClienteForm(instance=cliente)
        if access.read_only:
            disable_form_fields(form)
    context = {"form": form, "cliente": cliente, "back_url": back_url}
    context.update(access_context(access))
    return render(request, "clientes/form.html", context)


def eliminar_cliente(request, id: int):
    require_model_permission(request.user, Cliente, "delete")
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_lista")
    cliente = get_object_or_404(Cliente, pk=id)
    cliente.delete()
    return redirect(back_url)
