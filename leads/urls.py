from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('success/', views.success, name='success'),
     path('leads_data/', views.leads_data, name='leads_data'),
]
