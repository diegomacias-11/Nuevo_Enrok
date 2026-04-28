from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.scope import is_ventas_user

from .models import Cita


class VendedorUsuarioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class CitaForm(forms.ModelForm):
    fecha_cita = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
        required=True,
        label="Fecha de la cita",
    )

    class Meta:
        model = Cita
        fields = [
            "prospecto",
            "alianza",
            "giro",
            "tipo",
            "servicio",
            "servicio2",
            "servicio3",
            "contacto",
            "telefono",
            "correo",
            "conexion",
            "medio",
            "estatus_cita",
            "posibilidad",
            "fecha_cita",
            "numero_cita",
            "lugar",
            "estatus_seguimiento",
            "comentarios",
            "vendedor_usuario",
        ]
        labels = {
            "vendedor_usuario": "Vendedor",
        }
        field_classes = {
            "vendedor_usuario": VendedorUsuarioChoiceField,
        }
    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)


        user_model = get_user_model()
        vendedores_qs = (
            user_model.objects.filter(groups__name="Ventas", is_active=True)
            .distinct()
            .order_by("first_name", "last_name", "username")
        )
        self.fields["vendedor_usuario"].queryset = vendedores_qs
        self.fields["vendedor_usuario"].required = False

        if request_user and is_ventas_user(request_user):
            self.fields["vendedor_usuario"].queryset = user_model.objects.filter(pk=request_user.pk)
            self.fields["vendedor_usuario"].initial = request_user
            self.fields["vendedor_usuario"].disabled = True

        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_cita:
            local_dt = timezone.localtime(self.instance.fecha_cita)
            self.initial["fecha_cita"] = local_dt.strftime("%Y-%m-%dT%H:%M")
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None) and self.instance.fecha_registro:
            self.fecha_registro_display = timezone.localtime(self.instance.fecha_registro)
