from decimal import Decimal, ROUND_HALF_UP
from django import forms
from .models import Cliente


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
        # Hacer obligatorio comision_servicio
        if 'comision_servicio' in self.fields:
            self.fields['comision_servicio'].required = True
        # Mostrar porcentajes como enteros al editar
        if self.instance and getattr(self.instance, "pk", None) and not self.is_bound:
            for i in range(1, 11):
                key = f"comision{i}"
                val = getattr(self.instance, key, None)
                if val is not None:
                    # Mostrar con hasta 6 decimales (sin notación científica)
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
        # comision por servicio
        val_cs = cleaned.get("comision_servicio")
        if val_cs in (None, ""):
            self.add_error("comision_servicio", "Este campo es obligatorio.")
        else:
            try:
                dec = Decimal(val_cs)
                if dec > 1:
                    dec = (dec / Decimal("100")).quantize(Decimal("0.000001"))
                cleaned["comision_servicio"] = dec
            except Exception:
                self.add_error("comision_servicio", "Valor inválido.")
        total_comisionistas = Decimal("0")
        for i in range(1, 11):
            key = f"comision{i}"
            val = cleaned.get(key)
            if val is None:
                continue
            # si viene como porcentaje, dividir entre 100 (admite decimales)
            try:
                dec = Decimal(val)
            except Exception:
                continue
            # si el usuario captura 25 -> 0.25
            if dec > 1:
                dec = (dec / Decimal(100)).quantize(Decimal("0.000001"))
            cleaned[key] = dec
            total_comisionistas += dec
        # Validar que la suma de comisionistas no exceda ni sea menor a la comisión del servicio
        cs = cleaned.get("comision_servicio")
        if cs not in (None, ""):
            try:
                cs_dec = Decimal(cs)
                eps = Decimal("0.000001")
                if total_comisionistas > cs_dec + eps:
                    self.add_error(None, "La suma de porcentajes de comisionistas supera la comisión por servicio.")
                elif total_comisionistas + eps < cs_dec:
                    self.add_error(None, "La suma de porcentajes de comisionistas es menor que la comisión por servicio.")
            except Exception:
                pass
        return cleaned
