from django.urls import path
from . import views

urlpatterns = [
    path('recommend-careers/', views.generate_career_recommendations, name='generate_career_recommendations'),
    path('recommendations/latest/', views.get_latest_career_recommendation, name='get_latest_career_recommendation'),
]
