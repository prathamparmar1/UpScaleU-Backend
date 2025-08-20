from .views import QuizSubmitAPIView, UpdateCareerGoalAPIView
from django.urls import path, include

urlpatterns = [
    path('quiz/submit/', QuizSubmitAPIView.as_view(), name='quiz_submit'),
     path('update-career-goal/', UpdateCareerGoalAPIView.as_view(), name='update_career_goal'),
]
