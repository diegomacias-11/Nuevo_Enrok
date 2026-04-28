from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cita


@receiver(post_save, sender=Cita)
def crear_cliente_al_cerrar(sender, instance: Cita, created: bool, **kwargs):
    """
    Cuando una Cita queda en estatus_seguimiento 'Activo':
    - Si alianza es True, crea/actualiza una Alianza con nombre=prospecto y correo_electronico=correo.
    - Si alianza es False, crea/actualiza un Cliente con razon_social=prospecto y servicio.
    """
    if instance.estatus_seguimiento != "Activo":
        return

    if instance.alianza:
        try:
            from alianzas.models import Alianza
        except Exception:
            return
        alianza_data = {"nombre": instance.prospecto}
        if instance.correo:
            alianza_data["correo_electronico"] = instance.correo
        Alianza.objects.update_or_create(
            nombre=instance.prospecto,
            defaults=alianza_data,
        )
        return

    # Solo si alianza es False
    try:
        from clientes.models import Cliente
    except Exception:
        return

    servicio_value = None
    try:
        servicio_field = Cliente._meta.get_field("servicio")
        servicio_choices = {value for value, _label in servicio_field.choices}
    except Exception:
        servicio_choices = set()

    if instance.servicio in servicio_choices:
        servicio_value = instance.servicio
    elif servicio_choices:
        # Fallback al primer choice para no romper por validación
        servicio_value = next(iter(servicio_choices))

    if servicio_value is None:
        return

    Cliente.objects.update_or_create(
        razon_social=instance.prospecto,
        defaults={"servicio": servicio_value},
    )
