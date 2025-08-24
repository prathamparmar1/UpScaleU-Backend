from rest_framework import serializers
from .models import UserProfile, QuizSubmission

class QuizAnswerSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()

class QuizSubmitSerializer(serializers.Serializer):
    responses = QuizAnswerSerializer(many=True)
    
class QuizSubmissionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = ['id', 'answers', 'career_plan', 'submitted_at']

class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['career_goal']
