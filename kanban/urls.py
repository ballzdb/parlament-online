from django.urls import path

from . import views

app_name = 'kanban'

urlpatterns = [
    path('', views.board_list, name='board'),
    path('create/', views.card_create, name='card_create'),
    path('card/<int:pk>/', views.card_detail, name='card_detail'),
    path('card/<int:pk>/edit/', views.card_edit, name='card_edit'),
    path('<slug:slug>/', views.board_list, name='commission_board'),
]
