from django.urls import path

from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.moderation_queue, name='queue'),
    path('idea/<int:pk>/', views.moderate_idea, name='moderate_idea'),
    path('idea/<int:pk>/delete/', views.delete_idea, name='delete_idea'),
    path('sanctions/', views.sanctions, name='sanctions'),
    path('sanctions/<int:pk>/clear/', views.clear_sanction, name='clear_sanction'),
    path('rules/', views.moderation_rules, name='rules'),
]
