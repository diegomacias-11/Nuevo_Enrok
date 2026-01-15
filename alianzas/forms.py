from django import forms
from .models import Alianza

class AlianzaForm(forms.ModelForm):
    class Meta:
        model = Alianza
        fields = ['nombre', 'correo_electronico', 'correo_extra_1', 'correo_extra_2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
