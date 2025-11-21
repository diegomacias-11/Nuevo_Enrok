from django.urls import path
from . import views

urlpatterns = [
    path('', views.alianzas_lista, name='alianzas_lista'),
    path('nueva/', views.agregar_alianza, name='agregar_alianza'),
    path('editar/<int:id>/', views.editar_alianza, name='editar_alianza'),
    path('eliminar/<int:id>/', views.eliminar_alianza, name='eliminar_alianza'),
]
