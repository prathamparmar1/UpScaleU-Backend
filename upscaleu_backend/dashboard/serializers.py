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


class CareerRoadmapListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the "My Roadmaps" history list — summary info only,
    not the full phase-by-phase plan (use CareerRoadmapSerializer / the detail
    endpoint for that).
    """
    target_career = serializers.SerializerMethodField()
    is_fallback = serializers.SerializerMethodField()
    overall_progress_percent = serializers.SerializerMethodField()
    total_skills = serializers.SerializerMethodField()
    completed_skills = serializers.SerializerMethodField()

    class Meta:
        model = CareerRoadmap
        fields = [
            "id", "target_career", "created_at", "is_fallback",
            "overall_progress_percent", "total_skills", "completed_skills",
        ]

    def get_target_career(self, obj):
        return (obj.generated_roadmap or {}).get("target_career", "Unknown Career")

    def get_is_fallback(self, obj):
        return bool((obj.generated_roadmap or {}).get("is_fallback", False))

    def _progress(self, obj):
        # Computed once per object even though three method fields need it.
        if not hasattr(obj, "_cached_progress"):
            progress_obj, _ = RoadmapProgress.objects.get_or_create(user=obj.user, roadmap=obj)
            obj._cached_progress = compute_roadmap_progress(obj, progress_obj)
        return obj._cached_progress

    def get_overall_progress_percent(self, obj):
        return round(self._progress(obj)["overall"]["percent"], 1)

    def get_total_skills(self, obj):
        return self._progress(obj)["overall"]["total_skills"]

    def get_completed_skills(self, obj):
        return self._progress(obj)["overall"]["completed_skills"]

        
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