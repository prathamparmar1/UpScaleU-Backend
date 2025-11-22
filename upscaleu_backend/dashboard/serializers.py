from rest_framework import serializers
from .models import UserProfile, QuizSubmission,CareerRoadmap
from .models import SkillGapAnalysis

class QuizAnswerSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()

class QuizSubmitSerializer(serializers.Serializer):
    class Meta:
        model = QuizSubmission
        fields = ['answers', 'career_plan', 'submitted_at']
    
class QuizSubmissionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = ['id', 'answers', 'career_plan', 'submitted_at']

class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['career_goal']
    
#Roadmap Serializer
class CareerRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRoadmap
        fields = ['id', 'quiz_submission', 'generated_roadmap', 'created_at']
        
        
class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapAnalysis
        fields = "__all__"
        read_only_fields = ["user", "created_at"]


