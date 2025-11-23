from django.shortcuts import render
from .serializers import QuizSubmitSerializer, CareerGoalSerializer, QuizSubmissionHistorySerializer,CareerRoadmapSerializer,CareerRoadmap,SkillGapAnalysisSerializer, RoadmapProgressSerializer
from .utils import generate_career_plan
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import QuizSubmission ,UserProfile, CareerRoadmap, SkillGapAnalysis, RoadmapProgress
from .utils import generate_roadmap,analyze_skill_gaps # custom AI/rules-based generator
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from ai.models import CareerRecommendation
from .utils import build_roadmap_from_recommendation



class UpdateCareerGoalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = CareerGoalSerializer(profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Career goal updated successfully.', 'career_goal': profile.career_goal}, status=200)
        return Response(serializer.errors, status=400)
    
    
class QuizSubmitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuizSubmitSerializer(data=request.data)
        if serializer.is_valid():
            responses = serializer.validated_data['responses']
            try:
                plan = generate_career_plan(responses)
                QuizSubmission.objects.create(
                user=request.user,
                answers=responses,
                career_plan= plan
                )
            except Exception as e:
                return Response({'error': 'AI generation failed', 'details': str(e)}, status=500)
            
            return Response({'career_plan': plan}, status=200)
        
        return Response(serializer.errors, status=400)

class QuizHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # fetch all quiz submissions for logged-in user
        submissions = QuizSubmission.objects.filter(user=request.user).order_by('-submitted_at')
        serializer = QuizSubmissionHistorySerializer(submissions, many=True)
        return Response(serializer.data, status=200)
    
class LatestQuizSubmissionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        submission = QuizSubmission.objects.filter(user=request.user).order_by('-submitted_at').first()
        if not submission:
            return Response({'message': 'No quiz submission found.'}, status=404)

        serializer = QuizSubmissionHistorySerializer(submission)
        return Response(serializer.data, status=200)
  
    
#Roadmap View
class RoadmapGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Fetch latest quiz submission
            quiz_submission = QuizSubmission.objects.filter(user=request.user).order_by('-submitted_at').first()
            if not quiz_submission:
                return Response({"error": "No quiz submission found"}, status=400)

            # Call AI/Rules engine to generate roadmap
            roadmap_data = generate_roadmap(quiz_submission.answers, request.user)

            # Save in DB
            roadmap = CareerRoadmap.objects.create(
                user=request.user,
                quiz_submission=quiz_submission,
                generated_roadmap=roadmap_data
            )

            serializer = CareerRoadmapSerializer(roadmap)
            return Response(serializer.data, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class LatestRoadmapView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CareerRoadmapSerializer

    def get(self, request, *args, **kwargs):
        latest_roadmap = CareerRoadmap.objects.filter(user=request.user).order_by("-created_at").first()
        if not latest_roadmap:
            raise NotFound("No roadmap found for this user.")
        serializer = self.get_serializer(latest_roadmap)
        return Response(serializer.data)
    
# Dashboard Overview
class DashboardOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Career goal
        career_goal = user.userprofile.career_goal if hasattr(user, 'userprofile') else None

        # Latest quiz
        
        latest_quiz = QuizSubmission.objects.filter(user=request.user).order_by("-submitted_at").first()
        latest_quiz_data = QuizSubmissionHistorySerializer(latest_quiz).data if latest_quiz else None

        # Latest roadmap
        latest_roadmap = CareerRoadmap.objects.filter(user=request.user).order_by("-created_at").first()
        latest_roadmap_data = CareerRoadmapSerializer(latest_roadmap).data if latest_roadmap else None

        return Response({
            "career_goal": career_goal,
            "latest_quiz": latest_quiz_data,
            "latest_roadmap": latest_roadmap_data
        })
        

class SkillGapAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        career_goal = request.data.get("career_goal")
        current_skills = request.data.get("current_skills", [])

        if not career_goal:
            return Response({"error": "career_goal is required"}, status=400)
        if not isinstance(current_skills, list):
            return Response({"error": "current_skills must be a list"}, status=400)

        result = analyze_skill_gaps(career_goal, current_skills)

        # Save to DB
        analysis = SkillGapAnalysis.objects.create(
            user=request.user,
            career_goal=result["career_goal"],
            required_skills=result["required_skills"],
            current_skills=result["current_skills"],
            skill_gaps=result["skill_gaps"],
            recommendations=result["recommendations"],
        )

        serializer = SkillGapAnalysisSerializer(analysis)
        return Response(serializer.data, status=200)

class LatestSkillGapAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        analysis = (
            SkillGapAnalysis.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if not analysis:
            return Response({"message": "No skill gap analysis found."}, status=404)

        serializer = SkillGapAnalysisSerializer(analysis)
        return Response(serializer.data, status=200)

class RoadmapFromRecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # User can optionally specify which CareerRecommendation row to use
        rec_id = request.data.get("career_recommendation_id")

        if rec_id:
            try:
                rec = CareerRecommendation.objects.get(id=rec_id, user=request.user)
            except CareerRecommendation.DoesNotExist:
                return Response(
                    {"error": "CareerRecommendation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # use latest recommendation for this user
            rec = (
                CareerRecommendation.objects.filter(user=request.user)
                .order_by("-generated_at")
                .first()
            )
            if not rec:
                return Response(
                    {"error": "No career recommendations found for this user."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        rec_data = rec.recommendations  # JSON dict

        # ⭐ user choice: which career from the recommendations list
        selected_career = request.data.get("career")  # e.g. "DevOps Engineer"

        roadmap_data = build_roadmap_from_recommendation(
            rec_data,
            selected_career=selected_career
        )

        # create CareerRoadmap entry
        roadmap = CareerRoadmap.objects.create(
            user=request.user,
            quiz_submission=rec.quiz_submission,  # may be None
            generated_roadmap=roadmap_data,
        )

        serializer = CareerRoadmapSerializer(roadmap)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RoadmapProgressView(APIView):
    """
    GET current progress for a roadmap.
    If roadmap_id is passed as query param, use that.
    Otherwise, use latest roadmap for the user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roadmap_id = request.query_params.get("roadmap_id")

        if roadmap_id:
            try:
                roadmap = CareerRoadmap.objects.get(id=roadmap_id, user=request.user)
            except CareerRoadmap.DoesNotExist:
                return Response({"error": "Roadmap not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            roadmap = (
                CareerRoadmap.objects.filter(user=request.user)
                .order_by("-created_at")
                .first()
            )
            if not roadmap:
                return Response({"error": "No roadmap found for this user"}, status=status.HTTP_404_NOT_FOUND)

        progress, created = RoadmapProgress.objects.get_or_create(
            user=request.user,
            roadmap=roadmap
        )

        serializer = RoadmapProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkSkillCompletedAPIView(APIView):
    """
    POST to mark or unmark a skill as completed in a given roadmap.
    Body:
    {
      "roadmap_id": 3,
      "skill": "JavaScript",
      "completed": true   # or false
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roadmap_id = request.data.get("roadmap_id")
        skill = request.data.get("skill")
        completed = request.data.get("completed", True)

        if not roadmap_id or not skill:
            return Response(
                {"error": "roadmap_id and skill are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            roadmap = CareerRoadmap.objects.get(id=roadmap_id, user=request.user)
        except CareerRoadmap.DoesNotExist:
            return Response({"error": "Roadmap not found"}, status=status.HTTP_404_NOT_FOUND)

        progress, created = RoadmapProgress.objects.get_or_create(
            user=request.user,
            roadmap=roadmap
        )

        # validate that skill exists in roadmap
        skills_in_roadmap = []
        for phase in (roadmap.generated_roadmap or {}).get("phases", []):
            skills_in_roadmap.extend(phase.get("skills", []) or [])

        if skill not in skills_in_roadmap:
            return Response(
                {"error": f"Skill '{skill}' not found in this roadmap"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # update completed_skills
        completed_list = set(progress.completed_skills or [])

        if completed:
            completed_list.add(skill)
        else:
            if skill in completed_list:
                completed_list.remove(skill)

        progress.completed_skills = list(completed_list)
        progress.save()

        serializer = RoadmapProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)