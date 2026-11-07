from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<str:token>/', views.activate_account, name='activate'),
    path('reset/', views.request_password_reset, name='reset_request'),
    path('reset/<str:token>/', views.reset_password, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
]