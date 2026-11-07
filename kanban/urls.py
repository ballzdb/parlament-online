from django.urls import path

from . import views

app_name = 'kanban'

urlpatterns = [
    path('', views.board_list, name='board'),
    path('<slug:slug>/', views.board_list, name='commission_board'),
    path('card/<int:pk>/edit/', views.card_edit, name='card_edit'),
]