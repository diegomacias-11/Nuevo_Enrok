from django.urls import path

from . import views


app_name = "descargas"

urlpatterns = [
    path("construir/", views.construir_reporte, name="constructor"),
]
