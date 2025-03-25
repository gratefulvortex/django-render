from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.login_view, name='login'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('index/', views.index, name='index'),
    path('leads_data/', views.leads_data, name='leads_data'),
    path('master-dashboard/', views.master_dashboard, name='master_dashboard'),
    path('excel_data/', views.excel_data, name='excel_data'), # keep only this line
    path('alerts/', views.alerts_view, name='alerts'),
    path('toggle_interest/<int:lead_id>/', views.toggle_interest, name='toggle_interest'),
]