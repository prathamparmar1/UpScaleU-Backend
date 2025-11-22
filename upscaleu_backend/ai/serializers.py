from rest_framework import serializers
from .models import CareerRecommendation

class CareerRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRecommendation
        fields = ['id', 'user', 'recommendations', 'generated_at']
