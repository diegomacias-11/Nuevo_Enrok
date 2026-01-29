from datetime import date
from calendar import monthrange
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.template.loader import render_to_string
from dispersiones.models import Dispersion
from clientes.models import Cliente
from .models import Comision, PagoComision
from .forms import PagoComisionForm
from core.graph_email import send_graph_mail, GraphEmailError

MESES_NOMBRES = [
    "",
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def _coerce_mes_anio(request):
    today = date.today()
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    if not mes or not anio:
        return None, None, redirect(f"{request.path}?mes={today.month}&anio={today.year}")
    try:
        mes_i = int(mes)
        if mes_i < 1 or mes_i > 12:
            mes_i = today.month
    except Exception:
        mes_i = today.month
    try:
        anio_i = int(anio)
    except Exception:
        anio_i = today.year
    return mes_i, anio_i, None


def _first_day_next_month(y, m):
    if m == 12:
        return date(y + 1, 1, 1)
    return date(y, m + 1, 1)


def comisiones_lista(request):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir
    cliente_id = request.GET.get('cliente')

    # Recalcular liberaciones simples: Pagado => liberada
    Comision.objects.filter(periodo_mes=mes, periodo_anio=anio, dispersion__estatus_pago='Pagado').update(liberada=True, estatus_pago_dispersion='Pagado')
    Comision.objects.filter(periodo_mes=mes, periodo_anio=anio).exclude(dispersion__estatus_pago='Pagado').update(liberada=False)

    # Listado por comisionista con total del periodo
    qs_periodo = Comision.objects.filter(periodo_mes=mes, periodo_anio=anio)
    if cliente_id:
        qs_periodo = qs_periodo.filter(cliente_id=cliente_id)
    resumen = list(qs_periodo \
        .values('comisionista_id', 'comisionista__nombre') \
        .annotate(total=Sum('monto'), liberadas=Sum('monto', filter=Q(liberada=True))) \
        .order_by('comisionista__nombre'))

    # Pagos registrados para el periodo
    pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio) \
        .values('comisionista_id').annotate(pagos=Sum('monto'))
    if cliente_id:
        pagos = pagos.filter(comision__cliente_id=cliente_id)
    pagos_map = {p['comisionista_id']: p['pagos'] for p in pagos}
    for r in resumen:
        r['pagos'] = pagos_map.get(r['comisionista_id'], 0) or 0
        # Pendiente = liberado - pagos (no el total)
        r['pendiente'] = (r['liberadas'] or 0) - (r['pagos'] or 0)

    # Totales de la hoja (mes filtrado)
    total_periodo = qs_periodo.aggregate(v=Sum('monto'))['v'] or 0
    total_liberado = qs_periodo.filter(liberada=True).aggregate(v=Sum('monto'))['v'] or 0
    total_pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio).aggregate(v=Sum('monto'))['v'] or 0
    if cliente_id:
        total_pagos = PagoComision.objects.filter(
            periodo_mes=mes,
            periodo_anio=anio,
            comision__cliente_id=cliente_id,
        ).aggregate(v=Sum('monto'))['v'] or 0
    total_pendiente = total_liberado - total_pagos

    meses_choices = [(i, MESES_NOMBRES[i]) for i in range(1, 13)]
    context = {
        'mes': str(mes),
        'anio': str(anio),
        'cliente_id': str(cliente_id) if cliente_id else "",
        'clientes': Cliente.objects.order_by('razon_social'),
        'resumen': resumen,
        'meses': list(range(1, 13)),
        'meses_choices': meses_choices,
        'mes_nombre': MESES_NOMBRES[mes],
        'total_periodo': total_periodo,
        'total_liberado': total_liberado,
        'total_pagos': total_pagos,
        'total_pendiente': total_pendiente,
    }
    return render(request, 'comisiones/lista.html', context)


def comisiones_detalle(request, comisionista_id):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir
    context = _detalle_context(comisionista_id, mes, anio)
    return render(request, 'comisiones/detalle.html', context)


def registrar_pago(request, comisionista_id: int = None):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir and request.method != 'POST':
        return redir
    back_url = f"{reverse('comisiones_lista')}?mes={mes}&anio={anio}"
    comisiones_qs = Comision.objects.filter(
        periodo_mes=mes,
        periodo_anio=anio,
        pago_comision=False,
        estatus_pago_dispersion='Pagado',
    )
    comisionista_fixed = None
    if comisionista_id:
        comisiones_qs = comisiones_qs.filter(comisionista_id=comisionista_id)
        comisionista_fixed = comisiones_qs.select_related('comisionista').first()

    if request.method == 'POST':
        form = PagoComisionForm(request.POST, comisiones_qs=comisiones_qs, multi_mode=True)
        seleccion = request.POST.getlist("comisiones")
        if not seleccion:
            messages.error(request, "Selecciona al menos una comisiÃ³n.")
        elif form.is_valid():
            comisiones_sel = list(comisiones_qs.filter(id__in=seleccion))
            if len(comisiones_sel) != len(set(seleccion)):
                messages.error(request, "Hay comisiones invÃ¡lidas o ya pagadas.")
            else:
                with transaction.atomic():
                    pagos_crear = []
                    for comision in comisiones_sel:
                        pagos_crear.append(PagoComision(
                            comision=comision,
                            comisionista=comision.comisionista,
                            periodo_mes=comision.periodo_mes,
                            periodo_anio=comision.periodo_anio,
                            monto=comision.monto,
                            fecha_pago=form.cleaned_data.get("fecha_pago"),
                            comentario=form.cleaned_data.get("comentario"),
                        ))
                    PagoComision.objects.bulk_create(pagos_crear)
                    Comision.objects.filter(id__in=seleccion).update(pago_comision=True)
                if comisionista_id:
                    return redirect(reverse('comisiones_detalle', args=[comisionista_id]) + f"?mes={mes}&anio={anio}")
                return redirect(reverse('comisiones_lista') + f"?mes={mes}&anio={anio}")
    else:
        form = PagoComisionForm(comisiones_qs=comisiones_qs, multi_mode=True)
    return render(request, 'comisiones/pago_form.html', {
        'form': form,
        'back_url': back_url,
        'mes': mes,
        'anio': anio,
        'comisionista': comisionista_fixed.comisionista if comisionista_fixed else None,
        'mes_nombre': MESES_NOMBRES[mes],
        'comisiones_pendientes': comisiones_qs.select_related('cliente', 'comisionista'),
    })


def editar_pago(request, id: int):
    pago = get_object_or_404(PagoComision, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = f"{reverse('comisiones_detalle', args=[pago.comisionista_id])}?mes={mes}&anio={anio}"
    comisiones_qs = Comision.objects.filter(pk=pago.comision_id)
    if request.method == 'POST':
        form = PagoComisionForm(request.POST, instance=pago, comisiones_qs=comisiones_qs)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.comision = pago.comision
            obj.comisionista_id = pago.comisionista_id
            obj.periodo_mes = pago.comision.periodo_mes
            obj.periodo_anio = pago.comision.periodo_anio
            obj.monto = pago.comision.monto
            obj.save()
            return redirect(request.POST.get('next') or back_url)
    else:
        form = PagoComisionForm(instance=pago, comisiones_qs=comisiones_qs)
    return render(request, 'comisiones/pago_form.html', {
        'form': form,
        'back_url': back_url,
        'mes': mes,
        'anio': anio,
        'pago': pago,
        'comisionista': pago.comisionista,
    })


def eliminar_pago(request, id: int):
    pago = get_object_or_404(PagoComision, pk=id)
    mes, anio, _ = _coerce_mes_anio(request)
    back_url = request.POST.get('next') or f"{reverse('comisiones_detalle', args=[pago.comisionista_id])}?mes={mes}&anio={anio}"
    comision_id = pago.comision_id
    pago.delete()
    if comision_id:
        Comision.objects.filter(pk=comision_id).update(pago_comision=False)
    return redirect(back_url)


def _detalle_context(comisionista_id, mes, anio):
    qs = Comision.objects.filter(periodo_mes=mes, periodo_anio=anio, comisionista_id=comisionista_id) \
        .select_related('dispersion', 'cliente', 'comisionista')
    pagos = PagoComision.objects.filter(periodo_mes=mes, periodo_anio=anio, comisionista_id=comisionista_id).order_by('fecha_pago')
    total_periodo = qs.aggregate(v=Sum('monto'))['v'] or 0
    total_liberado = qs.filter(liberada=True).aggregate(v=Sum('monto'))['v'] or 0
    total_pagos = pagos.aggregate(v=Sum('monto'))['v'] or 0
    total_pendiente = total_liberado - total_pagos
    return {
        'mes': str(mes),
        'anio': str(anio),
        'comisionista': qs.first().comisionista if qs.exists() else None,
        'items': qs,
        'meses': list(range(1, 13)),
        'mes_nombre': MESES_NOMBRES[mes],
        'pagos': pagos,
        'total_periodo': total_periodo,
        'total_liberado': total_liberado,
        'total_pagos': total_pagos,
        'total_pendiente': total_pendiente,
    }


def enviar_detalle_comisionista(request, comisionista_id):
    mes, anio, redir = _coerce_mes_anio(request)
    if redir:
        return redir

    context = _detalle_context(comisionista_id, mes, anio)
    comisionista = context.get('comisionista')
    if not comisionista:
        messages.error(request, "No se encontraron comisiones para este comisionista.")
        return redirect(reverse('comisiones_lista') + f"?mes={mes}&anio={anio}")

    correos = comisionista.correos_para_envio()
    if not correos:
        messages.error(request, "El comisionista no tiene correo registrado.")
        return redirect(reverse('comisiones_detalle', args=[comisionista_id]) + f"?mes={mes}&anio={anio}")

    subject = f"Detalle de comisiones {context['mes_nombre']} {anio} - {comisionista.nombre}"
    html_body = render_to_string('comisiones/email_reporte.html', context)

    try:
        send_graph_mail(
            to=correos[0],
            subject=subject,
            html_body=html_body,
            cc=correos[1:] or None,
            bcc=settings.EMAIL_BCC_ALWAYS or None,
        )
        messages.success(request, f"Reporte enviado a {', '.join(correos)}.")
    except GraphEmailError as exc:
        messages.error(request, f"No se pudo enviar el correo: {exc}")
    except Exception as exc:  # pragma: no cover
        messages.error(request, f"No se pudo enviar el correo: {exc}")

    return redirect(reverse('comisiones_detalle', args=[comisionista_id]) + f"?mes={mes}&anio={anio}")
