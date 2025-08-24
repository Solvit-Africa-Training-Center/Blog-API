# ===== authentication/urls.py =====
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'authentication'

urlpatterns = [
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), #Login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # refresh
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Custom authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]