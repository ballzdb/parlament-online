from django.urls import path

from . import views

app_name = 'ideas'

urlpatterns = [
    path('', views.idea_list, name='list'),
    path('create/', views.idea_create, name='create'),
    path('<int:pk>/', views.idea_detail, name='detail'),
]