from django.urls import path
from . import views
app_name = 'moderation'
urlpatterns = [
    path('', views.moderation_queue, name='queue'),
    path('ideas/<int:pk>/review/', views.review_idea, name='review_idea'),
]
