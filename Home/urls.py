from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services_hub, name='services_hub'),
    path('blood-availability/', views.blood_availability, name='blood_availability'),
    path('blood-center-directory/', views.blood_center_directory, name='blood_center_directory'),
    path('camp-schedule/', views.camp_schedule, name='camp_schedule'),
    path('subscribe-camp-alert/', views.subscribe_camp_alert, name='subscribe_camp_alert'),
    path('register-camp-volunteer/', views.register_camp_volunteer, name='register_camp_volunteer'),

    path('donate/', views.donate, name='donate'),
    path('request-blood/', views.request_blood, name='request_blood'),
    path('contact/', views.contact, name='contact'),

    path('register/', views.register, name='register'),
    path("DonorRegisterData/", views.DonorRegisterData, name="DonorRegisterData"),
    path('logout/', views.logout_view, name='logout'),
    path('contectdata/', views.contectdata, name='ContectData'),
    path('DonateBloodData/', views.DonateBloodData, name='DonateBloodData'),
    path('RequestBloodData/', views.RequestBloodData, name='RequestBloodData'),
]
