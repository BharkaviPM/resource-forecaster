from django.urls import path
from .views import api_post_metrics

urlpatterns = [
    #...existing urls
    path('api/metrics/', api_post_metrics, name='api-post-metrics'),
]
