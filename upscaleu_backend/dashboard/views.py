from django.shortcuts import render
from .serializers import QuizSubmitSerializer, CareerGoalSerializer, QuizSubmissionHistorySerializer
from .utils import generate_career_plan
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import QuizSubmission ,UserProfile

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