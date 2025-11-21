from django import forms
from .models import PagoComision
from alianzas.models import Alianza


class PagoComisionForm(forms.ModelForm):
    comisionista = forms.ModelChoiceField(queryset=Alianza.objects.none())
    class Meta:
        model = PagoComision
        fields = [
            'comisionista',
            'fecha_pago',
            'monto',
            'comentario',
        ]
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure date input shows existing value in YYYY-MM-DD when editing
        if self.instance and getattr(self.instance, 'pk', None) and not self.is_bound:
            if self.instance.fecha_pago:
                self.initial['fecha_pago'] = self.instance.fecha_pago.isoformat()
