from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:pk>/open/', views.open_notification, name='open'),
]
