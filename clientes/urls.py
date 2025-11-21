from django.urls import path
from . import views

urlpatterns = [
    path('', views.clientes_lista, name='clientes_lista'),
    path('nuevo/', views.agregar_cliente, name='agregar_cliente'),
    path('editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),
]

