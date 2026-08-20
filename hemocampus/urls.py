from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from AdminZone import views as ad
from Home import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('Home.urls')),
    path('login/', views.login, name='login'),
    path('loginCode/', views.loginCode, name='loginCode'),
    path('LogoutPage/', views.LogoutPage, name='logout_page'),

    path('register/', views.register, name='register'),
    path('hospital_registration/', views.hospital_registration, name='hospital_registration'),

    # =========================
    # Admin Dashboard Routes
    # =========================
    path('Admin_Dashboard/', ad.dashboard, name='dashboard'),
    path('Blood_Stock/', ad.blood_stock, name='blood_stock'),
    path('Manage_Request/', ad.manage_request, name='manage_request'),
    path('Manage_Donors/', ad.manage_donors, name='manage_donors'),
    path('Report_Analytics/', ad.reports_analytics, name='reports_analytics'),
    path('Setting/', ad.settings, name='setting'),
    path('change_password/', ad.change_password, name='change_password'),

    # Admin POST Action Routes
    path('admin_action_donor/<int:donor_id>/<str:action>/', ad.admin_action_donor, name='admin_action_donor'),
    path('admin_action_request/<int:req_id>/<str:action>/', ad.admin_action_request, name='admin_action_request'),

    # =========================
    # Dashboards
    # =========================
    path('hospital-dashboard/', include('HospitalZone.urls')),
    path('donor-dashboard/', include('DonorZone.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)