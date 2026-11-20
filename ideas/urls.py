from django.urls import path

from . import views

app_name = 'ideas'

urlpatterns = [
    path('', views.idea_list, name='list'),
    path('create/', views.idea_create, name='create'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('events/archive/', views.event_archive, name='event_archive'),
    path('<int:pk>/delete/', views.idea_delete, name='delete'),
    path('<int:pk>/event/', views.event_create, name='event_create'),
    path('<int:pk>/', views.idea_detail, name='detail'),
]