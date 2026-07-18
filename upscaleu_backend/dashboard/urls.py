from .views import (QuizSubmitAPIView, UpdateCareerGoalAPIView, QuizHistoryView, LatestQuizSubmissionAPIView,
                     LatestRoadmapView, DashboardOverviewAPIView, SkillGapAnalysisAPIView,
                     LatestSkillGapAPIView, RoadmapFromRecommendationAPIView, RoadmapProgressView,
                     MarkSkillCompletedAPIView, RoadmapListAPIView, RoadmapDetailAPIView)
from django.urls import path, include

urlpatterns = [
    path('quiz/submit/', QuizSubmitAPIView.as_view(), name='quiz_submit'),
    path('update-career-goal/', UpdateCareerGoalAPIView.as_view(), name='update_career_goal'),
    path('quiz/history/', QuizHistoryView.as_view(), name="quiz-history"),
    path('quiz/history/latest/', LatestQuizSubmissionAPIView.as_view(), name="quiz-history-latest"),

    #Roadmap URLs
    path("roadmap/history/latest/", LatestRoadmapView.as_view(), name="latest-roadmap"),
    path("roadmap/history/", RoadmapListAPIView.as_view(), name="roadmap-history-list"),
    path("roadmap/<int:roadmap_id>/", RoadmapDetailAPIView.as_view(), name="roadmap-detail"),
    path("roadmap/from-recommendation/",RoadmapFromRecommendationAPIView.as_view(),name="roadmap-from-recommendation",
    ),

    #Dashboard Overview
    path("overview/", DashboardOverviewAPIView.as_view(), name="dashboard-overview"),
    path('skill-gap/', SkillGapAnalysisAPIView.as_view(), name='skill-gap'),
    path('skill-gap/latest/', LatestSkillGapAPIView.as_view(), name='latest-skill-gap'),
    path("roadmap/progress/", RoadmapProgressView.as_view(), name="roadmap-progress"),
    path("roadmap/progress/mark-skill/", MarkSkillCompletedAPIView.as_view(), name="roadmap-progress-mark-skill"),
]