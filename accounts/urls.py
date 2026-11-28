from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('verify/<int:pending_id>/<str:token>/', views.verify_email, name='verify_email'),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
    path('verification-resend/', views.resend_verification_email, name='resend_verification_email'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reset/', views.request_password_reset, name='reset_request'),
    path('profile/', views.profile_view, name='profile'),
    path('roles/', views.role_management, name='role_management'),
]