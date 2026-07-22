import json
import re

from ai.utils import call_gemini


def generate_career_plan(responses):
    # Simulate logic based on sample keywords in answers
    text = " ".join([r['answer'].lower() for r in responses])

    if "math" in text or "logic" in text:
        field = "Data Science"
        skills = ["Python", "SQL", "Machine Learning"]
        roadmap = [
            "Learn Python basics and data structures",
            "Study statistics and probability",
            "Explore SQL and databases",
            "Start with Machine Learning basics",
            "Build 2-3 projects using real datasets"
        ]
    elif "design" in text or "creativity" in text:
        field = "UI/UX Design"
        skills = ["Figma", "User Research", "Prototyping"]
        roadmap = [
            "Understand design principles and color theory",
            "Master Figma or Adobe XD",
            "Learn user research and usability testing",
            "Build design case studies",
            "Intern with startups to gain experience"
        ]
    else:
        field = "Software Engineering"
        skills = ["HTML", "CSS", "JavaScript", "Git"]
        roadmap = [
            "Learn HTML, CSS, and JavaScript",
            "Understand Git and GitHub",
            "Build simple websites and deploy them",
            "Study React or similar frameworks",
            "Contribute to open-source or freelance"
        ]

    return {
        "recommended_field": field,
        "skills_to_improve": skills,
        "learning_roadmap": roadmap
    }


def _build_skill_gap_prompt(career_goal, current_skills):
    """
    Ask Gemini to compare someone's current skills against what a specific career
    actually requires, and be concrete about both what's missing and what they
    already have going for them.
    """
    current_skills_text = ", ".join(current_skills) if current_skills else "(none listed)"

    prompt = f"""
You are a career mentor helping someone figure out exactly what stands between them
and working as a {career_goal}.

Their current self-reported skills: {current_skills_text}

Return ONLY a JSON object (no markdown fences, no extra text) with exactly this shape:
{{
  "career_goal": "{career_goal}",
  "required_skills": ["<specific skill 1>", "<specific skill 2>", "..."],
  "strengths": ["<skill from their current list that genuinely matters for this career>", "..."],
  "skill_gaps": [
    {{
      "skill": "<specific missing skill>",
      "why_it_matters": "<1-2 sentences, specific to this career, not generic>",
      "how_to_close": "<1-2 concrete sentences on how to build this skill through practice>"
    }}
  ],
  "action_items": [
    "<specific, ordered next step 1>",
    "<specific, ordered next step 2>",
    "<specific, ordered next step 3>"
  ]
}}

Rules:
- required_skills should be 6-10 skills a working professional in this exact career
  actually needs, named specifically (not vague categories).
- strengths should only include skills from their current list that are genuinely
  relevant to this career -- don't pad this list with unrelated skills.
- skill_gaps should only include required skills they don't already have. If their
  current skills already cover everything realistic, keep skill_gaps short and say so
  in the reasoning, don't invent gaps.
- Do NOT include course names, website names, or resource links -- just the plan.
""".strip()

    return prompt


def _fallback_skill_gap(career_goal, current_skills):
    """
    Used only if Gemini is unreachable or returns something unusable. Covers a wider
    set of careers than the old 3-career hardcoded map, and -- critically -- never
    silently returns an empty analysis for a career it doesn't recognize.
    """
    catalogue = {
        "full stack developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "PostgreSQL", "Git", "REST APIs"],
        "data scientist": ["Python", "Pandas", "NumPy", "Machine Learning", "SQL", "Statistics", "Data Visualization"],
        "mobile app developer": ["Kotlin", "Swift", "Flutter", "Firebase", "REST APIs", "UI Design Basics"],
        "ui/ux designer": ["Figma", "User Research", "Prototyping", "Wireframing", "Design Systems", "Usability Testing"],
        "data analyst": ["SQL", "Excel/Sheets", "Data Visualization", "Statistics", "Python or R"],
        "wildlife photographer": ["Photography", "Fieldcraft", "Photo Editing", "Wildlife Behavior Knowledge", "Patience/Endurance"],
        "furniture maker": ["Woodworking", "Design Sketching", "Tool Safety", "Joinery", "Finishing Techniques"],
        "ceramic artist": ["Wheel Throwing", "Glazing", "Kiln Firing", "Hand-Building", "Design Sensibility"],
        "event planner": ["Vendor Coordination", "Budgeting", "Client Communication", "Timeline Management"],
        "content creator": ["Video Editing", "Storytelling", "Consistency", "Basic SEO", "Audience Engagement"],
    }

    key = (career_goal or "").strip().lower()
    required_skills = catalogue.get(key)

    if not required_skills:
        # Unknown career: don't silently return an empty analysis. Give an honest,
        # generic competency baseline rather than pretending we know this career.
        required_skills = [
            "Core technical/craft fundamentals for this field",
            "Portfolio or demonstrable work samples",
            "Basic project/time management",
            "Communication with clients or collaborators",
            "Domain-specific tools relevant to this career",
        ]

    current_set = {s.strip().lower() for s in (current_skills or [])}
    required_lower = {s.lower(): s for s in required_skills}

    strengths = [orig for lower, orig in required_lower.items() if lower in current_set]
    gaps = [orig for lower, orig in required_lower.items() if lower not in current_set]

    skill_gaps = [
        {
            "skill": g,
            "why_it_matters": "",
            "how_to_close": "",
        }
        for g in gaps
    ]

    action_items = [f"Build hands-on practice with: {g}" for g in gaps[:3]] or [
        "Your listed skills already cover the fallback baseline for this career — "
        "try regenerating with AI for a more specific, career-tailored analysis."
    ]

    return {
        "career_goal": career_goal,
        "required_skills": required_skills,
        "current_skills": current_skills or [],
        "strengths": strengths,
        "skill_gaps": skill_gaps,
        "recommendations": {
            "is_fallback": True,
            "action_items": action_items,
            "strengths": strengths,
        },
    }


def analyze_skill_gaps(career_goal, current_skills):
    """
    Compare current_skills against what career_goal actually requires.
    Tries Gemini first for a career-specific analysis; falls back to a broader
    (but still real) rule-based comparison if Gemini is unavailable.
    """
    try:
        prompt = _build_skill_gap_prompt(career_goal, current_skills)
        raw = call_gemini(prompt, max_output_tokens=2048, temperature=0.5)

        try:
            parsed = json.loads(raw)
        except Exception:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                raise ValueError("No JSON object found in Gemini response")
            parsed = json.loads(m.group(0))

        required_skills = [str(s).strip() for s in (parsed.get("required_skills") or []) if str(s).strip()]
        if not required_skills:
            raise ValueError("AI skill gap analysis had no required_skills")

        strengths = [str(s).strip() for s in (parsed.get("strengths") or []) if str(s).strip()]

        skill_gaps = []
        for g in parsed.get("skill_gaps") or []:
            if not isinstance(g, dict):
                continue
            skill = str(g.get("skill") or "").strip()
            if not skill:
                continue
            skill_gaps.append({
                "skill": skill,
                "why_it_matters": str(g.get("why_it_matters") or "").strip(),
                "how_to_close": str(g.get("how_to_close") or "").strip(),
            })

        action_items = [str(a).strip() for a in (parsed.get("action_items") or []) if str(a).strip()]
        if not action_items:
            action_items = [f"Focus on: {g['skill']}" for g in skill_gaps[:3]]

        return {
            "career_goal": str(parsed.get("career_goal") or career_goal),
            "required_skills": required_skills,
            "current_skills": current_skills or [],
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "recommendations": {
                "is_fallback": False,
                "action_items": action_items,
                "strengths": strengths,
            },
        }

    except Exception:
        return _fallback_skill_gap(career_goal, current_skills)


# ---------------------------------------------------------------------------
# Real roadmap generation
# ---------------------------------------------------------------------------

def _build_roadmap_prompt(career, reason, required_skills, quiz_answers, career_goal, summary):
    """
    Build a prompt asking Gemini for a genuinely specific, actionable, phase-by-phase
    roadmap for ONE career — not a generic template with the career name swapped in.
    """
    answers_text = ""
    for idx, a in enumerate(quiz_answers or []):
        if isinstance(a, dict):
            answers_text += f"Q{idx + 1}: {a.get('question', '')}\nA: {a.get('answer', '')}\n"
        else:
            answers_text += f"Answer {idx + 1}: {str(a)}\n"
    if not answers_text:
        answers_text = "(No quiz answers available — write a strong general-purpose roadmap for this career.)"

    skills_text = ", ".join(required_skills) if required_skills else "(not specified — infer the right skills yourself)"

    prompt = f"""
You are a career mentor creating a roadmap for a student in India who wants to become a
{career}. Someone following this roadmap exactly should genuinely be job-ready or
practice-ready by the end of it — this is not a motivational overview, it is a real plan.

Context:
- Why this career was recommended to them: {reason or "Not specified"}
- Career goal they stated: {career_goal or "Not specified"}
- Overall AI summary of their profile: {summary or "Not specified"}
- Skills already identified as relevant: {skills_text}
- Their quiz answers:
{answers_text}

Write a roadmap with 5 to 6 sequential phases that together take a realistic amount of
time (typically 4 to 12 months total depending on the career's actual complexity — do not
default to a fixed number, reason about this specific career).

Rules for quality:
- Every phase description must be concrete: name real tools, techniques, or activities
  someone in THIS career actually uses, not generic phrases like "learn the basics" or
  "practice regularly."
- Each phase must end in a genuine, checkable milestone — something they can point to and
  say "I did this," not a vague feeling of progress (e.g. "Publish 3 finished woodworking
  pieces and photograph them for a portfolio," not "Get better at woodworking").
- suggested_actions must be specific, ordered, and doable — a to-do list, not advice.
- Skills should be named the way a working professional in this field would name them
  (specific tools/techniques), not vague categories.
- Do NOT include any course names, website names, or resource links — that will be added
  separately later. Just the plan itself.
- Assume the student has near-zero prior experience in this specific career unless their
  quiz answers suggest otherwise.

Return ONLY a JSON object (no markdown fences, no extra text) with exactly this shape:
{{
  "target_career": "{career}",
  "career_goal": "<career goal, or blank>",
  "summary": "<2-3 sentence overview of the path and what success looks like at the end>",
  "phases": [
    {{
      "name": "Phase 1: <short, specific phase title>",
      "duration_weeks": <integer>,
      "description": "<4-6 sentences: what they'll actually do in this phase, in plain
        natural language a student can follow, and why it matters for THIS career>",
      "milestone": "<one concrete, checkable deliverable that proves this phase is done>",
      "skills": ["<specific skill 1>", "<specific skill 2>", "<specific skill 3>"],
      "skill_details": [
        {{
          "skill": "<specific skill 1>",
          "why_it_matters": "<1-2 sentences>",
          "how_to_practice": "<1-2 concrete sentences — an exercise or activity, not a resource>"
        }}
      ],
      "suggested_actions": [
        "<specific, ordered action 1>",
        "<specific, ordered action 2>",
        "<specific, ordered action 3>"
      ]
    }}
  ]
}}
""".strip()

    return prompt


def _postprocess_ai_roadmap(parsed, career, career_goal):
    """
    Validate and normalize the AI's roadmap JSON so it always matches the contract
    the frontend expects, and inject empty `resources` slots for future use.
    Raises on anything unusable, so the caller can fall back safely.
    """
    phases_in = parsed.get("phases")
    if not isinstance(phases_in, list) or not phases_in:
        raise ValueError("AI roadmap has no usable phases")

    clean_phases = []
    for p in phases_in:
        name = str(p.get("name") or "Untitled Phase").strip()
        try:
            duration_weeks = int(p.get("duration_weeks") or 4)
        except (TypeError, ValueError):
            duration_weeks = 4
        duration_weeks = max(1, min(duration_weeks, 26))  # sanity clamp: 1-26 weeks/phase

        description = str(p.get("description") or "").strip()
        milestone = str(p.get("milestone") or "").strip()

        skill_details_in = p.get("skill_details") or []
        skill_details = []
        for sd in skill_details_in:
            if not isinstance(sd, dict):
                continue
            skill_name = str(sd.get("skill") or "").strip()
            if not skill_name:
                continue
            skill_details.append({
                "skill": skill_name,
                "why_it_matters": str(sd.get("why_it_matters") or "").strip(),
                "how_to_practice": str(sd.get("how_to_practice") or "").strip(),
                "resources": [],  # populated by a future feature — intentionally empty for now
            })

        # `skills` must stay a flat list of strings -- this is the exact contract the
        # frontend checkbox/progress logic relies on. Derive it from skill_details when
        # possible so the two stay consistent; fall back to whatever `skills` was given.
        if skill_details:
            skills = [sd["skill"] for sd in skill_details]
        else:
            skills = [str(s).strip() for s in (p.get("skills") or []) if str(s).strip()]

        if not skills:
            # A phase with zero skills breaks progress tracking -- skip it rather than
            # silently showing an empty checklist.
            continue

        suggested_actions = [str(a).strip() for a in (p.get("suggested_actions") or []) if str(a).strip()]
        if not suggested_actions:
            suggested_actions = ["Work through the skills listed above in order, and keep notes on what you build."]

        clean_phases.append({
            "name": name,
            "duration_weeks": duration_weeks,
            "description": description or f"Build the skills for this stage of becoming a {career}.",
            "milestone": milestone or "Complete and review the skills in this phase before moving on.",
            "skills": skills,
            "skill_details": skill_details,
            "suggested_actions": suggested_actions,
        })

    if not clean_phases:
        raise ValueError("AI roadmap had phases but none were usable after validation")

    total_weeks = sum(p["duration_weeks"] for p in clean_phases)

    return {
        "target_career": str(parsed.get("target_career") or career),
        "career_goal": str(parsed.get("career_goal") or career_goal or ""),
        "summary": str(parsed.get("summary") or "").strip(),
        "estimated_total_duration_weeks": total_weeks,
        "phases": clean_phases,
        "is_fallback": False,
    }


def _fallback_detailed_roadmap(career, required_skills, reason, summary, career_goal):
    """
    Used only if Gemini is unreachable or returns something unusable.
    Still career-specific (uses the career name and required_skills throughout) and
    still has 5 real phases with milestones -- not a 3-step skill-splitter.
    """
    skills = [s for s in (required_skills or []) if s] or ["Core fundamentals", "Practical tools", "Applied technique"]

    def _chunk(lst, n):
        if not lst:
            return [[] for _ in range(n)]
        k, m = divmod(len(lst), n)
        result, idx = [], 0
        for i in range(n):
            size = k + (1 if i < m else 0)
            chunk = lst[idx:idx + size] or [lst[i % len(lst)]]
            result.append(chunk)
            idx += size
        return result

    foundation, core, applied, advanced = _chunk(skills, 4)

    def phase(name, weeks, description, milestone, phase_skills, actions):
        return {
            "name": name,
            "duration_weeks": weeks,
            "description": description,
            "milestone": milestone,
            "skills": phase_skills,
            "skill_details": [
                {"skill": s, "why_it_matters": "", "how_to_practice": "", "resources": []}
                for s in phase_skills
            ],
            "suggested_actions": actions,
        }

    phases = [
        phase(
            "Phase 1: Orientation & Foundations",
            3,
            f"Get a real, grounded understanding of what working as a {career} actually "
            f"involves day-to-day, then start building the most basic skills this path "
            f"depends on: {', '.join(foundation)}. The goal here is removing guesswork "
            f"about the field before investing serious time in it.",
            f"Write a one-page summary, in your own words, of what a {career} does day-to-day "
            f"and which of your foundation skills you've started practicing.",
            foundation,
            [
                f"Research 3 real people currently working as a {career} and note what their day looks like.",
                f"Start daily short practice sessions (20-30 min) on: {', '.join(foundation)}.",
                "Keep a simple log of what you practiced each day and what felt hardest.",
            ],
        ),
        phase(
            "Phase 2: Core Skill Building",
            6,
            f"Move from basic exposure to deliberate, focused practice on the core skills "
            f"a {career} relies on most: {', '.join(core)}. This phase is about repetition "
            f"with feedback -- doing the same core actions enough times that they stop "
            f"feeling effortful.",
            f"Demonstrate each core skill ({', '.join(core)}) in a small, standalone exercise "
            f"you can show someone else.",
            core,
            [
                f"Break each of {', '.join(core)} into weekly practice goals.",
                "After each practice session, note one specific thing to improve next time.",
                "Get feedback from at least one person more experienced than you, if possible.",
            ],
        ),
        phase(
            "Phase 3: Applied Practice & First Real Projects",
            6,
            f"Apply everything so far to 1-2 real, self-directed projects that resemble "
            f"actual {career} work -- not exercises, but something with a real output at "
            f"the end. This is where skills stop being separate and start combining.",
            f"Finish at least one complete project that uses {', '.join(applied)} together, "
            f"start to finish.",
            applied,
            [
                "Pick a project small enough to finish in 2-4 weeks, not one that needs months.",
                f"Deliberately use {', '.join(applied)} together in that project.",
                "Document the process as you go -- this becomes portfolio material later.",
            ],
        ),
        phase(
            "Phase 4: Specialization & Advanced Work",
            6,
            f"Go deeper into the areas of {career} work that are harder, more specialized, "
            f"or more valuable: {', '.join(advanced)}. This is where you start to "
            f"differentiate yourself from someone with only beginner-level ability.",
            f"Complete one piece of work that specifically required {', '.join(advanced)} "
            f"and would be difficult for a beginner to produce.",
            advanced,
            [
                f"Identify which part of {career} work you enjoyed most in Phase 3, and go deeper there.",
                f"Practice {', '.join(advanced)} through harder, more ambiguous problems than before.",
                "Seek out one piece of real critique on your advanced work, not just encouragement.",
            ],
        ),
        phase(
            "Phase 5: Portfolio & Real-World Readiness",
            4,
            f"Package everything you've built into something a real employer, client, or "
            f"collaborator could evaluate -- this phase is about presentation and "
            f"credibility, not new skills.",
            f"Have a portfolio (physical, digital, or both depending on the field) with your "
            f"best 2-3 pieces of work, plus a short pitch explaining your path to becoming a {career}.",
            ["Portfolio presentation", "Personal pitch / story", "Outreach basics"],
            [
                "Select your 2-3 strongest pieces of work from Phases 3 and 4.",
                "Write a short, honest narrative of your journey and what you can now do.",
                f"Reach out to 5 people or organizations connected to {career} work and share what you've built.",
            ],
        ),
    ]

    total_weeks = sum(p["duration_weeks"] for p in phases)

    return {
        "target_career": career,
        "career_goal": career_goal or "",
        "summary": summary or (
            f"A structured path from zero experience to real, demonstrable ability as a "
            f"{career}, built around deliberate practice and real project work rather than "
            f"passive learning."
        ),
        "estimated_total_duration_weeks": total_weeks,
        "phases": phases,
        "is_fallback": True,
    }


def build_roadmap_from_recommendation(rec_data, selected_career=None, quiz_answers=None):
    """
    Build a real, detailed, career-specific roadmap from the AI career recommendation JSON.

    Tries Gemini first for a genuinely tailored plan; falls back to a still-detailed,
    still career-specific rule-based roadmap if Gemini is unavailable or returns
    something unusable. The return shape is unchanged from before, so the frontend
    (roadmap.jsx) needs no changes:

    {
      "target_career": "...",
      "career_goal": "...",
      "summary": "...",
      "estimated_total_duration_weeks": 25,
      "phases": [
        {
          "name": "...", "duration_weeks": 4, "description": "...", "milestone": "...",
          "skills": ["...", ...], "skill_details": [...], "suggested_actions": [...]
        },
        ...
      ]
    }
    """
    if not rec_data:
        return {"message": "No recommendation data provided."}

    recommendations = rec_data.get("recommendations", [])
    if not isinstance(recommendations, list) or not recommendations:
        return {"message": "No recommendations list found in data."}

    chosen = None

    if selected_career:
        sel_lower = selected_career.strip().lower()
        for r in recommendations:
            if str(r.get("career", "")).strip().lower() == sel_lower:
                chosen = r
                break

    if chosen is None:
        chosen = sorted(recommendations, key=lambda r: r.get("score", 0), reverse=True)[0]

    career = chosen.get("career", "Unknown Career")
    reason = chosen.get("reason", "")
    required_skills = chosen.get("required_skills", [])
    summary = rec_data.get("summary", "")
    career_goal = rec_data.get("career_goal", "")

    try:
        prompt = _build_roadmap_prompt(career, reason, required_skills, quiz_answers, career_goal, summary)
        raw = call_gemini(prompt, max_output_tokens=4096, temperature=0.6)

        try:
            parsed = json.loads(raw)
        except Exception:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                raise ValueError("No JSON object found in Gemini response")
            parsed = json.loads(m.group(0))

        return _postprocess_ai_roadmap(parsed, career, career_goal)

    except Exception:
        return _fallback_detailed_roadmap(career, required_skills, reason, summary, career_goal)


def compute_roadmap_progress(roadmap, progress_obj):
    """
    Compute progress stats for a given CareerRoadmap and RoadmapProgress.
    - roadmap.generated_roadmap is the JSON we created earlier with phases/skills.
    - progress_obj.completed_skills is a list of skill names the user has marked done.
    """
    data = roadmap.generated_roadmap or {}
    phases = data.get("phases", [])

    completed_skills = set(progress_obj.completed_skills or [])

    total_skills = 0
    completed_count = 0
    per_phase = []

    for phase in phases:
        phase_name = phase.get("name", "Unnamed Phase")
        skills = phase.get("skills", []) or []

        phase_total = len(skills)
        total_skills += phase_total

        phase_completed = 0
        for s in skills:
            if s in completed_skills:
                phase_completed += 1

        completed_count += phase_completed

        phase_progress = {
            "phase_name": phase_name,
            "total_skills": phase_total,
            "completed_skills": phase_completed,
            "percent": (phase_completed / phase_total * 100) if phase_total > 0 else 0,
        }
        per_phase.append(phase_progress)

    overall_percent = (completed_count / total_skills * 100) if total_skills > 0 else 0

    return {
        "overall": {
            "total_skills": total_skills,
            "completed_skills": completed_count,
            "percent": overall_percent,
        },
        "phases": per_phase,
    }


# import openai
# from django.conf import settings

# def generate_career_plan(responses):
#     prompt = "Based on the following quiz answers, suggest a career path, skills to improve, and learning roadmap:\n\n"
#     for item in responses:
#         prompt += f"Q: {item['question']}\nA: {item['answer']}\n\n"

#     prompt += "Now, based on these, give a detailed career mentorship plan."

#     openai.api_key = settings.OPENAI_API_KEY

#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )

#     return response.choices[0].message.content