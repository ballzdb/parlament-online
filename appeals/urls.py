from django.urls import path

from . import views

app_name = 'appeals'

urlpatterns = [
    path('', views.appeal_list, name='list'),
    path('create/', views.appeal_create, name='create'),
    path('<int:pk>/manage/', views.appeal_manage, name='manage'),
]