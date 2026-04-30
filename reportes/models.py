from django.db import models


class Reporte(models.Model):
    class Meta:
        managed = False
        default_permissions = ("view",)
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
