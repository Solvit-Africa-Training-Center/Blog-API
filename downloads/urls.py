# downloads/urls.py 

from django.urls import path
from . import views

app_name = 'downloads'

urlpatterns = [
    path('historical-posts/', views.HistoricalPostsDownloadView.as_view(), name='historical_posts'),
    path('my-posts/', views.UserPostsDownloadView.as_view(), name='my_posts'),
    path('usage-stats/', views.DownloadUsageView.as_view(), name='usage_stats'),
]