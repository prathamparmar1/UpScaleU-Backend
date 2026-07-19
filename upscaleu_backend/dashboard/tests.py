from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from .models import QuizSubmission, UserProfile, CareerRoadmap, RoadmapProgress
from .utils import compute_roadmap_progress, build_roadmap_from_recommendation, _fallback_detailed_roadmap


class QuizSubmitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quizuser", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_submit_creates_quiz_submission_without_calling_dead_mock(self):
        payload = {
            "responses": [
                {"question": "What excites you?", "answer": "Building things with my hands"},
                {"question": "Risk tolerance?", "answer": "I want steady, predictable growth"},
            ]
        }
        resp = self.client.post("/api/dash/quiz/submit/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

        submission = QuizSubmission.objects.get(user=self.user)
        self.assertEqual(len(submission.answers), 2)
        # career_plan should no longer be populated by the removed mock generator
        self.assertEqual(submission.career_plan, {})

    def test_submit_rejects_malformed_payload(self):
        resp = self.client.post("/api/dash/quiz/submit/", {"responses": "not-a-list"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateCareerGoalTests(TestCase):
    def test_works_even_without_preexisting_userprofile(self):
        user = User.objects.create_user(username="goaluser", password="pass12345")
        self.assertFalse(UserProfile.objects.filter(user=user).exists())

        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.put(
            "/api/dash/update-career-goal/", {"career_goal": "Wildlife Photographer"}, format="json"
        )
        # This is the exact bug that was fixed: UserProfile.objects.get() would 500
        # here since no profile row existed yet. get_or_create() should make this pass.
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.career_goal, "Wildlife Photographer")


class RoadmapFallbackTests(TestCase):
    def test_fallback_roadmap_has_five_real_phases(self):
        result = _fallback_detailed_roadmap(
            career="Ceramic Artist",
            required_skills=["Wheel throwing", "Glazing", "Kiln firing"],
            reason="Leans toward the Makers archetype",
            summary="",
            career_goal="",
        )
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["target_career"], "Ceramic Artist")
        self.assertEqual(len(result["phases"]), 5)
        for phase in result["phases"]:
            self.assertIn("milestone", phase)
            self.assertGreater(len(phase["skills"]), 0)
            # resources slot must exist and be empty, ready for a future feature
            for sd in phase["skill_details"]:
                self.assertEqual(sd["resources"], [])
        total = sum(p["duration_weeks"] for p in result["phases"])
        self.assertEqual(result["estimated_total_duration_weeks"], total)

    @patch("dashboard.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_build_roadmap_from_recommendation_falls_back_on_gemini_failure(self, mock_call):
        rec_data = {
            "career_goal": "",
            "summary": "",
            "recommendations": [
                {
                    "career": "Wildlife Photographer",
                    "reason": "Explorer archetype",
                    "score": 85,
                    "required_skills": ["Photography", "Fieldcraft", "Photo editing"],
                }
            ],
        }
        result = build_roadmap_from_recommendation(rec_data, selected_career="Wildlife Photographer")
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["target_career"], "Wildlife Photographer")
        self.assertGreaterEqual(len(result["phases"]), 5)

    def test_returns_message_when_no_recommendations_present(self):
        result = build_roadmap_from_recommendation({"recommendations": []})
        self.assertIn("message", result)


class ComputeRoadmapProgressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="progressuser", password="pass12345")
        self.quiz = QuizSubmission.objects.create(user=self.user, answers=[])
        self.roadmap = CareerRoadmap.objects.create(
            user=self.user,
            quiz_submission=self.quiz,
            generated_roadmap={
                "phases": [
                    {"name": "Phase 1", "skills": ["A", "B"]},
                    {"name": "Phase 2", "skills": ["C"]},
                ]
            },
        )

    def test_zero_percent_when_nothing_completed(self):
        progress = RoadmapProgress.objects.create(user=self.user, roadmap=self.roadmap, completed_skills=[])
        result = compute_roadmap_progress(self.roadmap, progress)
        self.assertEqual(result["overall"]["total_skills"], 3)
        self.assertEqual(result["overall"]["completed_skills"], 0)
        self.assertEqual(result["overall"]["percent"], 0)

    def test_partial_completion_percentage(self):
        progress = RoadmapProgress.objects.create(
            user=self.user, roadmap=self.roadmap, completed_skills=["A", "C"]
        )
        result = compute_roadmap_progress(self.roadmap, progress)
        self.assertEqual(result["overall"]["completed_skills"], 2)
        self.assertAlmostEqual(result["overall"]["percent"], 200 / 3, places=2)
        # Phase 2 (single skill "C") should show 100% even though overall isn't done
        phase_2 = result["phases"][1]
        self.assertEqual(phase_2["percent"], 100.0)


class RoadmapHistoryScopingTests(TestCase):
    """Roadmap history/detail endpoints must never leak another user's data."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        quiz = QuizSubmission.objects.create(user=self.owner, answers=[])
        self.roadmap = CareerRoadmap.objects.create(
            user=self.owner,
            quiz_submission=quiz,
            generated_roadmap={"target_career": "Data Analyst", "phases": []},
        )
        self.client = APIClient()

    def test_owner_can_list_their_own_roadmap(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get("/api/dash/roadmap/history/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["target_career"], "Data Analyst")

    def test_other_user_sees_empty_list(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get("/api/dash/roadmap/history/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)

    def test_other_user_cannot_fetch_roadmap_detail_by_id(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(f"/api/dash/roadmap/{self.roadmap.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_fetch_their_roadmap_detail(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(f"/api/dash/roadmap/{self.roadmap.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], self.roadmap.id)


class RoadmapRateLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="spammer", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        from ai.models import CareerRecommendation
        self.quiz = QuizSubmission.objects.create(user=self.user, answers=[])
        self.rec = CareerRecommendation.objects.create(
            user=self.user,
            quiz_submission=self.quiz,
            recommendations={
                "recommendations": [
                    {"career": "Data Analyst", "reason": "", "score": 80, "required_skills": ["SQL"]},
                ]
            },
        )

    @patch("dashboard.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_blocks_after_twelve_calls_in_window(self, mock_call):
        url = "/api/dash/roadmap/from-recommendation/"
        for _ in range(12):
            resp = self.client.post(url, {"career": "Data Analyst"}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        resp = self.client.post(url, {"career": "Data Analyst"}, format="json")
        self.assertEqual(resp.status_code, 429)
        self.assertIn("retry_after_seconds", resp.data)

    @patch("dashboard.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_allowed_again_once_window_passes(self, mock_call):
        url = "/api/dash/roadmap/from-recommendation/"
        for _ in range(12):
            self.client.post(url, {"career": "Data Analyst"}, format="json")

        CareerRoadmap.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(minutes=61)
        )

        resp = self.client.post(url, {"career": "Data Analyst"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)