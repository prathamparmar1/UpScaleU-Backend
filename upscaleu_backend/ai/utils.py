import os
import re
import json
import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-pro"

# The 8 archetypes the quiz is built around. Naming these explicitly in the prompt
# is what actually lets the model recommend careers beyond the usual handful —
# without this, "career recommendation assistant" defaults to Software Engineer /
# Doctor / Data Scientist almost every time, regardless of quiz answers.
ARCHETYPES = {
    "Makers": "build with their hands — trades, crafts, physical products",
    "Connectors": "work closely with people — coordination, service, relationships",
    "Explorers": "thrive outdoors or off-script — fieldwork, travel, nature",
    "Screen Workers": "create digitally — software, design, content, data",
    "Thinkers": "solve and analyze — research, science, strategy",
    "Performers": "express and entertain — arts, media, public presence",
    "Healers": "care for others — health, therapy, support roles",
    "Builders": "start and grow things — entrepreneurship, business, ventures",
}


def check_rate_limit(queryset, timestamp_field, window_minutes, max_calls):
    """
    Rolling-window rate limit based on counting existing rows in the DB, rather than
    a cache backend — this means it works correctly even if Render runs multiple
    gunicorn workers (no need for Redis/shared cache to be configured).

    queryset: an already-user-filtered queryset of a model with a timestamp field
              (e.g. CareerRecommendation.objects.filter(user=request.user))
    timestamp_field: name of that model's timestamp field, e.g. "generated_at"
    window_minutes: size of the rolling window
    max_calls: how many calls are allowed within that window

    Returns None if the caller is within the limit.
    Returns a dict with an "error" message and "retry_after_seconds" if they've hit it.
    """
    cutoff = timezone.now() - timedelta(minutes=window_minutes)
    recent_qs = queryset.filter(**{f"{timestamp_field}__gte": cutoff}).order_by(timestamp_field)
    count = recent_qs.count()

    if count < max_calls:
        return None

    oldest_in_window = recent_qs.first()
    oldest_time = getattr(oldest_in_window, timestamp_field)
    retry_after = (oldest_time + timedelta(minutes=window_minutes)) - timezone.now()
    retry_after_seconds = max(int(retry_after.total_seconds()), 1)

    return {
        "error": (
            f"You've hit the limit of {max_calls} requests per {window_minutes} minutes. "
            f"This protects our AI quota — please try again in a bit."
        ),
        "retry_after_seconds": retry_after_seconds,
    }


def build_recommendation_prompt(quiz_answers, user_profile):
    """
    Build a prompt asking Gemini to return structured JSON with career recommendations,
    grounded in a wide space of real careers rather than the handful of "obvious" options.
    """
    answers_text = ""
    for idx, a in enumerate(quiz_answers or []):
        if isinstance(a, dict):
            answers_text += f"Q{idx + 1}: {a.get('question', '')}\nA: {a.get('answer', '')}\n"
        else:
            answers_text += f"Answer {idx + 1}: {str(a)}\n"

    career_goal = getattr(user_profile, "career_goal", "") or ""
    archetype_lines = "\n".join(f"- {name}: {desc}" for name, desc in ARCHETYPES.items())

    prompt = f"""
You are a career guidance assistant for students and early-career professionals in India.
Your job is to widen their sense of what's possible, not just confirm the handful of careers
they already know about (engineer, doctor, generic "software developer", etc).

The quiz below maps a person's interests across 8 broad career archetypes:
{archetype_lines}

Use the person's answers to infer which archetype(s) they lean toward, then recommend SPECIFIC,
real careers that fit — including less commonly discussed ones when they genuinely match
(e.g. within Makers: furniture maker, ceramic artist; within Explorers: wildlife photographer,
drone pilot; within Thinkers: behavioural economist, UX researcher; within Builders: SaaS
founder, franchise owner). Recommendations should feel personally reasoned from their specific
answers, not generic. Prefer variety across archetypes over five near-identical tech roles,
unless their answers overwhelmingly point to one archetype.

Output a JSON object EXACTLY (no markdown fences, no extra text) with this shape:
{{
  "career_goal": "<the user's stated career goal, or blank if none>",
  "recommendations": [
    {{
      "career": "<specific career name>",
      "reason": "<one to two sentences tying this back to their actual answers>",
      "score": <0-100 integer suitability score>,
      "required_skills": ["skill1", "skill2", "skill3"]
    }}
  ],
  "summary": "<one short paragraph summarizing their overall profile>"
}}

Return between 4 and 6 recommendations, ranked by score descending.

User's stated career goal (may be blank): {career_goal}

Quiz answers:
{answers_text}

Return ONLY the JSON object described above.
""".strip()

    return prompt


def call_gemini(prompt, max_output_tokens=2048, temperature=0.7):
    """
    Call Google Gemini's generateContent endpoint, requesting native JSON output
    so we don't have to regex-extract JSON out of prose.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=45)
    resp.raise_for_status()
    result = resp.json()

    try:
        candidates = result.get("candidates", [])
        if not candidates:
            raise RuntimeError("No candidates in Gemini response")
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise RuntimeError("No parts in Gemini response")
        raw_text = parts[0].get("text", "")
        if not raw_text:
            raise RuntimeError("Empty text in Gemini response")
        return raw_text
    except Exception as e:
        raise RuntimeError(f"Unexpected Gemini response format: {result}") from e


def _fallback_recommendations(quiz_answers, user_profile):
    """
    Used only when Gemini is unreachable or GEMINI_API_KEY is missing.
    Scores each of the 8 archetypes by simple keyword overlap with the user's answers,
    so the fallback at least reflects their quiz instead of always saying
    "Software Engineer".
    """
    text = " ".join(
        (a.get("answer") if isinstance(a, dict) else str(a)) for a in (quiz_answers or [])
    ).lower()

    keyword_map = {
        "Makers": ["hands", "build", "craft", "material", "physical", "workshop"],
        "Connectors": ["people", "conversation", "coordinat", "negotiat", "event", "help someone"],
        "Explorers": ["outdoor", "trail", "field", "travel", "nature", "unpredictable"],
        "Screen Workers": ["screen", "code", "design tool", "digital", "app", "software", "data"],
        "Thinkers": ["understand why", "puzzle", "research", "analy", "math", "structured"],
        "Performers": ["audience", "perform", "stage", "camera", "laugh", "expression"],
        "Healers": ["care", "heal", "support", "recover", "volunteer", "counsel"],
        "Builders": ["business", "risk", "money", "start", "found", "grow"],
    }

    scores = {name: 0 for name in ARCHETYPES}
    for name, keywords in keyword_map.items():
        for kw in keywords:
            if kw in text:
                scores[name] += 1

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_archetypes = [name for name, count in ranked if count > 0][:2] or ["Screen Workers"]

    catalogue = {
        "Makers": [
            {"career": "Furniture Maker / Woodworker", "required_skills": ["Woodworking", "Design sketching", "Tool safety"]},
            {"career": "Jewellery Designer", "required_skills": ["Metalwork or beadwork", "Sketching", "Small business basics"]},
        ],
        "Connectors": [
            {"career": "Event / Wedding Planner", "required_skills": ["Vendor coordination", "Budgeting", "Client communication"]},
            {"career": "HR Consultant", "required_skills": ["Recruitment basics", "Communication", "Employment policy"]},
        ],
        "Explorers": [
            {"career": "Wildlife Photographer", "required_skills": ["Photography", "Patience/fieldcraft", "Photo editing"]},
            {"career": "Trekking / Adventure Guide", "required_skills": ["First aid", "Navigation", "Group leadership"]},
        ],
        "Screen Workers": [
            {"career": "Full-Stack Web Developer", "required_skills": ["JavaScript", "APIs", "Databases"]},
            {"career": "UI/UX Designer", "required_skills": ["Figma", "User research", "Prototyping"]},
        ],
        "Thinkers": [
            {"career": "Data Analyst", "required_skills": ["SQL", "Excel/Sheets", "Data visualization"]},
            {"career": "UX Researcher", "required_skills": ["User interviews", "Synthesis", "Reporting"]},
        ],
        "Performers": [
            {"career": "YouTube Creator / Content Producer", "required_skills": ["Video editing", "Storytelling", "Consistency"]},
            {"career": "Voice-Over Artist", "required_skills": ["Voice control", "Basic audio editing", "Scriptreading"]},
        ],
        "Healers": [
            {"career": "Nutritionist / Dietitian", "required_skills": ["Nutrition science", "Client counselling", "Meal planning"]},
            {"career": "Occupational Therapist", "required_skills": ["Patient care", "Rehabilitation techniques", "Empathy"]},
        ],
        "Builders": [
            {"career": "SaaS Founder", "required_skills": ["Product thinking", "Basic coding or no-code tools", "Sales"]},
            {"career": "E-commerce / Reseller Business Owner", "required_skills": ["Sourcing", "Marketing", "Basic finance"]},
        ],
    }

    recommendations = []
    score_value = 85
    for archetype in top_archetypes:
        for item in catalogue.get(archetype, []):
            recommendations.append({
                "career": item["career"],
                "reason": f"Your answers leaned toward the '{archetype}' archetype, which this career fits well.",
                "score": score_value,
                "required_skills": item["required_skills"],
            })
            score_value -= 5

    if not recommendations:
        recommendations = [{
            "career": "Full-Stack Web Developer",
            "reason": "A broad, in-demand starting point while we gather more signal on your interests.",
            "score": 75,
            "required_skills": ["Programming fundamentals", "Data structures", "Web basics"],
        }]

    summary = (
        f"Based on your answers, you lean toward the {' and '.join(top_archetypes)} "
        f"archetype(s)."
    )

    return {
        "career_goal": getattr(user_profile, "career_goal", "") or "",
        "recommendations": recommendations,
        "summary": summary,
        "is_fallback": True,
    }


def generate_recommendations(quiz_answers, user_profile):
    """
    Try to call Gemini. If it fails or the key is missing, fall back to an
    archetype-aware, keyword-scored mock (not a single hardcoded default).
    Returns (parsed_dict, prompt, raw_response).
    """
    prompt = build_recommendation_prompt(quiz_answers, user_profile)

    try:
        raw_resp = call_gemini(prompt)
        try:
            parsed = json.loads(raw_resp)
            parsed.setdefault("is_fallback", False)
            return parsed, prompt, raw_resp
        except Exception:
            # Native JSON mode should make this unnecessary, but keep it as a safety net
            # in case the model still wraps the JSON in prose.
            m = re.search(r"\{.*\}", raw_resp, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    parsed.setdefault("is_fallback", False)
                    return parsed, prompt, raw_resp
                except Exception:
                    pass
            raise RuntimeError("Failed to parse Gemini response as JSON.")
    except Exception:
        parsed = _fallback_recommendations(quiz_answers, user_profile)
        return parsed, prompt, "fallback-response"