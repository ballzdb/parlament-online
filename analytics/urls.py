from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('classes/', views.classes, name='classes'),
    path('anonymous-event/', views.collect_anonymous_page_view, name='anonymous_event'),
]