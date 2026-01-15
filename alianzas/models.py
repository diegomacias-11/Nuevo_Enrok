from django.db import models

class Alianza(models.Model):
    nombre = models.CharField(max_length=100)
    correo_electronico = models.EmailField(null=True, blank=True)
    correo_extra_1 = models.EmailField(null=True, blank=True)
    correo_extra_2 = models.EmailField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if self.nombre is not None:
            self.nombre = self.nombre.strip().upper()
        super().save(*args, **kwargs)

    def correos_para_envio(self):
        correos = [
            self.correo_electronico,
            self.correo_extra_1,
            self.correo_extra_2,
        ]
        return [c.strip() for c in correos if c and c.strip()]
