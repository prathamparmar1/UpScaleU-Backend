from django.db import models
from django.conf import settings

class CareerRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="career_recommendations")
    generated_at = models.DateTimeField(auto_now_add=True)

    # store the structured recommendation returned by AI (list of careers and reasons, scores, etc.)
    recommendations = models.JSONField()

    # optional: store which quiz_submission was used
    quiz_submission = models.ForeignKey("dashboard.QuizSubmission", on_delete=models.SET_NULL, null=True, blank=True)

    # optionally keep raw prompt/response for debugging
    raw_prompt = models.TextField(blank=True, null=True)
    raw_response = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"CareerRecommendation {self.id} for {self.user.username} @ {self.generated_at}"
