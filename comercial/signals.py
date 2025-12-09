from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Cita


@receiver(post_save, sender=Cita)
def crear_cliente_al_cerrar(sender, instance: Cita, created: bool, **kwargs):
    """
    Cuando una Cita queda en estatus_seguimiento 'Activo',
    crea/actualiza un Cliente con razon_social (prospecto) y servicio.
    """
    try:
        from clientes.models import Cliente
    except Exception:
        return

    if instance.estatus_seguimiento != "Activo":
        return

    servicio_value = None
    try:
        servicio_choices = {choice.value for choice in Cliente.Servicio}
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
