from rest_framework import serializers
from .models import UserProfile

class QuizAnswerSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()

class QuizSubmitSerializer(serializers.Serializer):
    responses = QuizAnswerSerializer(many=True)

class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['career_goal']
