from django.urls import path

from . import views

app_name = 'ideas'

urlpatterns = [
    path('feedback/', views.research_feedback, name='research_feedback'),
    path('', views.idea_list, name='list'),
    path('create/', views.idea_create, name='create'),
    path('events/', views.event_list, name='events'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('<int:pk>/delete/', views.idea_delete, name='delete'),
    path('<int:pk>/event/', views.event_create, name='event_create'),
    path('<int:pk>/', views.idea_detail, name='detail'),
]
