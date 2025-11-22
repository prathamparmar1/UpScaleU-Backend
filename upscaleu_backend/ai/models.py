from django.db import models
from django.contrib.auth.models import User

class CareerRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recommendations = models.JSONField()  # [{"career": "Data Scientist", "confidence": 0.92, "reason": "..."}]
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Career Recommendations for {self.user.username}"
