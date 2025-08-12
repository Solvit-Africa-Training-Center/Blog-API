# ===== comments/urls.py =====
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'comments'

router = DefaultRouter()
router.register(r'', views.CommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
]