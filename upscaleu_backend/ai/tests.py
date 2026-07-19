from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from .models import CareerRecommendation
from . import utils as ai_utils
from dashboard.models import QuizSubmission


class FallbackRecommendationsTests(TestCase):
    def test_fallback_flags_is_fallback_true_and_has_valid_shape(self):
        answers = [{"question": "q", "answer": "I love building things with my hands"}]
        result = ai_utils._fallback_recommendations(answers, None)
        self.assertTrue(result["is_fallback"])
        self.assertGreater(len(result["recommendations"]), 0)
        for rec in result["recommendations"]:
            self.assertIn("career", rec)
            self.assertIn("reason", rec)
            self.assertIn("score", rec)
            self.assertIn("required_skills", rec)

    def test_fallback_leans_toward_matching_archetype(self):
        answers = [{
            "question": "q",
            "answer": "I love volunteering to help and heal people, care and support them",
        }]
        result = ai_utils._fallback_recommendations(answers, None)
        careers = [r["career"] for r in result["recommendations"]]
        self.assertTrue(any("Nutritionist" in c or "Therapist" in c for c in careers))

    def test_fallback_never_crashes_on_empty_answers(self):
        result = ai_utils._fallback_recommendations([], None)
        self.assertTrue(result["is_fallback"])
        self.assertGreater(len(result["recommendations"]), 0)


class GenerateRecommendationsTests(TestCase):
    @patch("ai.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_falls_back_gracefully_when_gemini_unavailable(self, mock_call):
        answers = [{"question": "q", "answer": "I enjoy solving technical problems"}]
        parsed, prompt, raw = ai_utils.generate_recommendations(answers, None)
        self.assertTrue(parsed["is_fallback"])
        self.assertEqual(raw, "fallback-response")
        self.assertIn("recommendations", parsed)

    @patch("ai.utils.call_gemini")
    def test_marks_successful_gemini_response_as_not_fallback(self, mock_call):
        mock_call.return_value = (
            '{"career_goal": "", "summary": "test", "recommendations": '
            '[{"career": "UX Researcher", "reason": "fits", "score": 90, '
            '"required_skills": ["Interviews"]}]}'
        )
        answers = [{"question": "q", "answer": "I like understanding people"}]
        parsed, prompt, raw = ai_utils.generate_recommendations(answers, None)
        self.assertFalse(parsed["is_fallback"])
        self.assertEqual(parsed["recommendations"][0]["career"], "UX Researcher")


class RecommendCareersRateLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ratelimituser", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        QuizSubmission.objects.create(
            user=self.user,
            answers=[{"question": "q", "answer": "I enjoy building things"}],
        )

    @patch("ai.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_blocks_after_six_calls_in_window(self, mock_call):
        url = "/api/ai/recommend-careers/"
        for _ in range(6):
            resp = self.client.post(url, {}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, 429)
        self.assertIn("retry_after_seconds", resp.data)
        self.assertIn("error", resp.data)

    @patch("ai.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_allowed_again_once_window_passes(self, mock_call):
        url = "/api/ai/recommend-careers/"
        for _ in range(6):
            self.client.post(url, {}, format="json")

        CareerRecommendation.objects.filter(user=self.user).update(
            generated_at=timezone.now() - timedelta(minutes=61)
        )

        resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @patch("ai.utils.call_gemini", side_effect=RuntimeError("no network in tests"))
    def test_unauthenticated_request_rejected(self, mock_call):
        anon_client = APIClient()
        resp = anon_client.post("/api/ai/recommend-careers/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class RateLimitHelperTests(TestCase):
    """Unit-level tests for the shared check_rate_limit() helper itself."""

    def setUp(self):
        self.user = User.objects.create_user(username="helperuser", password="pass12345")
        self.quiz = QuizSubmission.objects.create(user=self.user, answers=[])

    def _make_recommendation(self):
        return CareerRecommendation.objects.create(
            user=self.user,
            quiz_submission=self.quiz,
            recommendations={"recommendations": []},
        )

    def test_none_returned_when_under_limit(self):
        self._make_recommendation()
        result = ai_utils.check_rate_limit(
            CareerRecommendation.objects.filter(user=self.user),
            "generated_at",
            window_minutes=60,
            max_calls=6,
        )
        self.assertIsNone(result)

    def test_blocked_when_at_limit(self):
        for _ in range(6):
            self._make_recommendation()
        result = ai_utils.check_rate_limit(
            CareerRecommendation.objects.filter(user=self.user),
            "generated_at",
            window_minutes=60,
            max_calls=6,
        )
        self.assertIsNotNone(result)
        self.assertIn("retry_after_seconds", result)
        self.assertGreater(result["retry_after_seconds"], 0)

    def test_old_entries_outside_window_dont_count(self):
        for _ in range(6):
            self._make_recommendation()
        CareerRecommendation.objects.filter(user=self.user).update(
            generated_at=timezone.now() - timedelta(minutes=61)
        )
        result = ai_utils.check_rate_limit(
            CareerRecommendation.objects.filter(user=self.user),
            "generated_at",
            window_minutes=60,
            max_calls=6,
        )
        self.assertIsNone(result)