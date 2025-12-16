from datetime import datetime, time

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .models import Cliente
from .forms import ClienteForm
from django.contrib import messages
from decimal import Decimal


def clientes_lista(request):
    q = (request.GET.get("q") or "").strip()
    fecha_desde = request.GET.get("fecha_desde") or ""
    fecha_hasta = request.GET.get("fecha_hasta") or ""

    qs = Cliente.objects.all()
    if q:
        qs = qs.filter(razon_social__icontains=q)
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
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    }
    return render(request, "clientes/lista.html", context)


def agregar_cliente(request):
    back_url = request.GET.get("next") or reverse("clientes_lista")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ClienteForm()
    return render(request, "clientes/form.html", {"form": form, "back_url": back_url})


def editar_cliente(request, id: int):
    cliente = get_object_or_404(Cliente, pk=id)
    back_url = request.GET.get("next") or reverse("clientes_lista")
    if request.method == "POST":
        back_url = request.POST.get("next") or back_url
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect(back_url)
    else:
        form = ClienteForm(instance=cliente)
        # Quitar advertencia en GET: ahora la validación se hace en el formulario y bloquea guardado
    return render(request, "clientes/form.html", {"form": form, "cliente": cliente, "back_url": back_url})


def eliminar_cliente(request, id: int):
    back_url = request.POST.get("next") or request.GET.get("next") or reverse("clientes_lista")
    cliente = get_object_or_404(Cliente, pk=id)
    cliente.delete()
    return redirect(back_url)
