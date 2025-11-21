from django.urls import path
from . import views

urlpatterns = [
    path('', views.dispersiones_lista, name='dispersiones_lista'),
    path('nueva/', views.agregar_dispersion, name='agregar_dispersion'),
    path('editar/<int:id>/', views.editar_dispersion, name='editar_dispersion'),
    path('eliminar/<int:id>/', views.eliminar_dispersion, name='eliminar_dispersion'),
]

