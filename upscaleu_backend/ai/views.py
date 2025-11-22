from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import CareerRecommendationSerializer
from .models import CareerRecommendation
from dashboard.models import QuizSubmission, UserProfile
from .utils import generate_recommendations

class RecommendCareersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Optionally accept quiz_submission id in body to use a specific submission
        quiz_id = request.data.get("quiz_submission_id")
        quiz_submission = None
        if quiz_id:
            try:
                quiz_submission = QuizSubmission.objects.get(id=quiz_id, user=request.user)
            except QuizSubmission.DoesNotExist:
                return Response({"error": "quiz_submission not found"}, status=404)
        else:
            # use latest quiz
            quiz_submission = QuizSubmission.objects.filter(user=request.user).order_by("-submitted_at").first()

        # If no quiz data found, allow client to submit quiz answers directly
        if not quiz_submission:
            quiz_answers = request.data.get("responses", [])
        else:
            quiz_answers = quiz_submission.answers

        # fetch user profile (to get career_goal)
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None

        try:
            parsed, prompt, raw_resp = generate_recommendations(quiz_answers, user_profile)
        except Exception as e:
            return Response({"error": "AI generation failed", "details": str(e)}, status=500)

        # Save result
        rec = CareerRecommendation.objects.create(
            user=request.user,
            recommendations=parsed,
            quiz_submission=quiz_submission,
            raw_prompt=prompt,
            raw_response=(raw_resp if isinstance(raw_resp, str) else str(raw_resp))
        )

        serializer = CareerRecommendationSerializer(rec)
        return Response(serializer.data, status=201)


class LatestRecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rec = CareerRecommendation.objects.filter(user=request.user).order_by("-generated_at").first()
        if not rec:
            return Response({"message": "No recommendations found."}, status=404)
        serializer = CareerRecommendationSerializer(rec)
        return Response(serializer.data, status=200)
