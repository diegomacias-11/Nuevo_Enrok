
from django.urls import path
from . import views

urlpatterns = [
    path('', views.reportes_home, name='reportes_home'),
    path('citas/', views.dashboard_citas, name='reportes_dashboard_citas'),
    path('dispersiones/', views.dashboard_dispersiones, name='reportes_dashboard_dispersiones'),
    path('comisiones/', views.dashboard_comisiones, name='reportes_dashboard_comisiones'),
]
