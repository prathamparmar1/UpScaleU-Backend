from rest_framework import serializers
from .models import UserProfile, QuizSubmission,CareerRoadmap
from .models import SkillGapAnalysis, RoadmapProgress
from .utils import compute_roadmap_progress

class QuizAnswerSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()

class QuizSubmitSerializer(serializers.Serializer):
    responses = QuizAnswerSerializer(many=True)
        
class QuizSubmissionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = ['id', 'answers', 'career_plan', 'submitted_at']
        read_only_fields = ['id', 'submitted_at']

class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['career_goal']
    
#Roadmap Serializer
class CareerRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRoadmap
        fields = ["id", "user", "quiz_submission", "generated_roadmap", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
        
        
class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapAnalysis
        fields = "__all__"
        read_only_fields = ["user", "created_at"]
        
class RoadmapProgressSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = RoadmapProgress
        fields = ["id", "roadmap", "completed_skills", "completed_phases", "created_at", "updated_at", "progress"]
        read_only_fields = ["id", "created_at", "updated_at", "progress"]

    def get_progress(self, obj):
        return compute_roadmap_progress(obj.roadmap, obj)


