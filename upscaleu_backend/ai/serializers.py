from rest_framework import serializers
from .models import CareerRecommendation

class CareerRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRecommendation
        fields = ['id', 'generated_at', 'recommendations', 'quiz_submission', 'raw_prompt']
        read_only_fields = ['id', 'generated_at', 'raw_prompt']
