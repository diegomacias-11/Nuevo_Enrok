from decimal import Decimal, ROUND_HALF_UP
from django import forms
from .models import Cliente

PERCENT_Q = Decimal("0.000001")

def _percent_to_fraction(val):
    return (Decimal(val) / Decimal("100")).quantize(PERCENT_Q)


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "razon_social",
            "servicio",
            "comision_servicio",
            # pares 1..10
            *[f"comisionista{i}" for i in range(1, 11)],
            *[f"comision{i}" for i in range(1, 11)],
        ]
        widgets = {
            **{f"comision{i}": forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}) for i in range(1, 11)},
            "comision_servicio": forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # comision_servicio se calcula como suma de comisiones
        if 'comision_servicio' in self.fields:
            self.fields['comision_servicio'].required = False
            self.fields['comision_servicio'].disabled = True
        # Mostrar porcentajes como enteros al editar
        if self.instance and getattr(self.instance, "pk", None) and not self.is_bound:
            for i in range(1, 11):
                key = f"comision{i}"
                val = getattr(self.instance, key, None)
                if val is not None:
                    # Mostrar con hasta 6 decimales (sin notaci?n cient?fica)
                    percent = (Decimal(val) * Decimal(100)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                    self.initial[key] = format(percent, 'f')
            # comision por servicio
            val = getattr(self.instance, "comision_servicio", None)
            if val is not None:
                percent = (Decimal(val) * Decimal(100)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                self.initial["comision_servicio"] = format(percent, 'f')
        # Asegurar step=1 e inputmode numeric
        for i in range(1, 11):
            f = f"comision{i}"
            if f in self.fields:
                self.fields[f].widget.attrs["step"] = "any"
                self.fields[f].widget.attrs["inputmode"] = "decimal"
        self.fields["comision_servicio"].widget.attrs["step"] = "any"
        self.fields["comision_servicio"].widget.attrs["inputmode"] = "decimal"

    def clean(self):
        cleaned = super().clean()
        total_comisionistas = Decimal("0")
        for i in range(1, 11):
            key = f"comision{i}"
            val = cleaned.get(key)
            if val in (None, ""):
                continue
            try:
                dec = _percent_to_fraction(val)
            except Exception:
                self.add_error(key, "Valor inv?lido.")
                continue
            cleaned[key] = dec
            total_comisionistas += dec
        if total_comisionistas > Decimal("1"):
            self.add_error(None, "La suma de comisiones no puede exceder 100%.")
        cleaned["comision_servicio"] = total_comisionistas
        return cleaned
