from django.urls import path

from . import views

app_name = 'moderation'

urlpatterns = [
    path('', views.moderation_queue, name='queue'),
    path('idea/<int:pk>/', views.moderate_idea, name='moderate_idea'),
]
