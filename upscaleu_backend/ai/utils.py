import os
import requests
import json
from django.conf import settings

GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", "")
print("GEMINI_API_KEY loaded:",GEMINI_API_KEY)  # for debugging only

def build_recommendation_prompt(quiz_answers, user_profile):
    """
    Build a prompt asking the model to return structured JSON with career recommendations.
    We instruct the model to respond in strict JSON with keys: recommendations: [{career, reason, score, required_skills}], summary.
    """
    # convert quiz answers list->string for prompt
    answers_text = ""
    for idx, a in enumerate(quiz_answers or []):
        # if answer is dict with question/answer:
        if isinstance(a, dict):
            answers_text += f"Q{idx+1}: {a.get('question','')}\nA: {a.get('answer','')}\n"
        else:
            answers_text += f"Answer {idx+1}: {str(a)}\n"

    career_goal = getattr(user_profile, "career_goal", "")

    prompt = f"""
You are a career recommendation assistant. Given the user's quiz answers and current career goal, output a JSON object EXACTLY (no extra text) with:
{{
  "career_goal": "<the user's career goal or blank>",
  "recommendations": [
    {{
      "career": "<career name>",
      "reason": "<one-line reason why it's a good fit>",
      "score": <0-100 integer suitability score>,
      "required_skills": ["skill1","skill2",...]
    }},
    ...
  ],
  "summary": "<one-paragraph high-level summary>"
}}

User career_goal: {career_goal}
Quiz answers:
{answers_text}

Return ONLY the JSON object.
    """.strip()

    return prompt

def call_gemini(prompt, max_tokens=800):
    """
    Call Google Gemini (Generative Language API) generateContent endpoint.
    Docs pattern:
    POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=API_KEY
    Body:
    { "contents": [ { "parts": [ { "text": "your prompt" } ] } ] }
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    # Typical shape:
    # {
    #   "candidates": [
    #     {
    #       "content": {
    #         "parts": [
    #           { "text": "..." }
    #         ]
    #       }
    #     }
    #   ]
    # }
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
        # if shape is different, dump whole result for debugging
        raise RuntimeError(f"Unexpected Gemini response format: {result}") from e

def generate_recommendations(quiz_answers, user_profile):
    """
    Try to call Gemini. If it fails or key missing, fall back to simple rule-based mock.
    Return a dict: {career_goal, recommendations: [...], summary}
    """
    prompt = build_recommendation_prompt(quiz_answers, user_profile)

    # Attempt Gemini call, but be defensive
    try:
        raw_resp = call_gemini(prompt)
        # raw_resp should be JSON text — try to parse
        try:
            parsed = json.loads(raw_resp)
            return parsed, prompt, raw_resp
        except Exception:
            # If model returned plain text, try to extract JSON substring
            import re
            m = re.search(r"\{.*\}", raw_resp, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    return parsed, prompt, raw_resp
                except Exception:
                    pass
            # fallback to mock
            raise RuntimeError("Failed to parse Gemini response as JSON.")
    except Exception as e:
        # fallback rule-based (simple)
        text = " ".join([ (a.get("answer") if isinstance(a, dict) else str(a)) for a in (quiz_answers or []) ])
        text_lower = text.lower()
        if "math" in text_lower or "data" in text_lower or "python" in text_lower:
            recommendations = [
                {"career": "Data Scientist", "reason": "Strong quantitative interest", "score": 90, "required_skills": ["Python", "Pandas", "Machine Learning"]},
                {"career": "Data Analyst", "reason": "Good for analytical skills", "score": 80, "required_skills": ["SQL","Excel","Python"]},
            ]
            summary = "Based on answers, data-related careers are a strong fit. Start with Python, statistics and SQL."
        elif "design" in text_lower or "ux" in text_lower or "creative" in text_lower:
            recommendations = [
                {"career": "UI/UX Designer", "reason": "Creative and user-focused", "score": 88, "required_skills": ["Figma","User Research","Prototyping"]},
            ]
            summary = "Design roles suit creativity — focus on building case studies."
        else:
            recommendations = [
                {"career": "Software Engineer", "reason": "General software building interest", "score": 85, "required_skills": ["Programming fundamentals","Data structures","System design"]},
            ]
            summary = "A general software engineering path fits. Build projects and learn core CS topics."

        parsed = {
            "career_goal": getattr(user_profile, "career_goal", ""),
            "recommendations": recommendations,
            "summary": summary
        }
        return parsed, prompt, "mock-response"
