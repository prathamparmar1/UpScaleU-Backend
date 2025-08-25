from .views import QuizSubmitAPIView, UpdateCareerGoalAPIView, QuizHistoryView, LatestQuizSubmissionAPIView, RoadmapGenerateAPIView,LatestRoadmapView
from django.urls import path, include

urlpatterns = [
    path('quiz/submit/', QuizSubmitAPIView.as_view(), name='quiz_submit'),
    path('update-career-goal/', UpdateCareerGoalAPIView.as_view(), name='update_career_goal'),
    path('quiz/history/', QuizHistoryView.as_view(), name="quiz-history"),
    path('quiz/history/latest/', LatestQuizSubmissionAPIView.as_view(), name="quiz-history-latest"),

    #Roadmap URLs
    path('roadmap/generate/', RoadmapGenerateAPIView.as_view(), name='roadmap-generate'),
     path("roadmap/history/latest/", LatestRoadmapView.as_view(), name="latest-roadmap"),
]
