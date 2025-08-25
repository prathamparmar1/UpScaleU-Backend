from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class QuizSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField()
    career_plan = models.JSONField()

    def __str__(self):
        return f"{self.user.username} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    career_goal = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

#Roadmap model..

class CareerRoadmap(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz_submission = models.ForeignKey("QuizSubmission", on_delete=models.CASCADE)
    generated_roadmap = models.JSONField()  # step-by-step roadmap
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Roadmap for {self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"