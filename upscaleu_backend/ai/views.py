from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import CareerRecommendation
from .serializers import CareerRecommendationSerializer
from dashboard.models import QuizSubmission, SkillGapAnalysis, UserProfile  # assuming models exist
import openai
import os
from openai import OpenAI
from dotenv import load_dotenv
import os

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# response = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content": "You are an AI career advisor."},
#         {"role": "user", "content": "Suggest career paths for a data science student."}
#     ]
# )

# print(response.choices[0].message.content)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_career_recommendations(request):
    user = request.user

    try:
        latest_quiz = QuizSubmission.objects.filter(user=user).latest('submitted_at')
        latest_skill_gap = SkillGapAnalysis.objects.filter(user=user).latest('created_at')
        career_goal = UserProfile.career_goal
    except Exception:
        return Response({"error": "Missing required data for recommendation generation."}, status=400)

    # Combine user data for AI prompt
    prompt = f"""
    User Profile:
    Career Goal: {career_goal}

    Quiz Performance Summary:
    {latest_quiz.career_plan}

    Skill Gaps:
    {latest_skill_gap.skill_gaps}

    Based on this data, suggest 3-5 suitable career paths with a confidence score (0-1)
    and a one-line reason for each.
    Respond strictly in JSON format as:
    [
        {{"career": "Data Scientist", "confidence": 0.95, "reason": "Strong analytical skills and data interest"}},
        ...
    ]
    """

    try:
        ai_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI career advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = ai_response.choices[0].message['content']
        recommendations = eval(content)  # You can replace eval with json.loads for safety
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    # Save in DB
    career_recommendation = CareerRecommendation.objects.create(
        user=user,
        recommendations=recommendations
    )

    serializer = CareerRecommendationSerializer(career_recommendation)
    return Response(serializer.data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_career_recommendation(request):
    user = request.user
    try:
        latest_recommendation = CareerRecommendation.objects.filter(user=user).latest('generated_at')
    except CareerRecommendation.DoesNotExist:
        return Response({"message": "No career recommendations found."}, status=404)

    serializer = CareerRecommendationSerializer(latest_recommendation)
    return Response(serializer.data)