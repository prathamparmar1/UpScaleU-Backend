from django.urls import path
from .views import RecommendCareersAPIView, LatestRecommendationAPIView

urlpatterns = [
    path("recommend-careers/", RecommendCareersAPIView.as_view(), name="ai-recommend-careers"),
    path("recommendations/latest/", LatestRecommendationAPIView.as_view(), name="ai-latest-recommendation"),
]
