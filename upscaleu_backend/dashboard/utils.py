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


def generate_roadmap(answers, user):
    """
    Placeholder roadmap generator.
    In real-world: integrate OpenAI / custom ML pipeline.
    """

    # Example: just a structured mock roadmap
    return {
        "career_goal": "Software Engineer",
        "steps": [
            {"step": 1, "title": "Learn Python", "resources": ["RealPython", "LeetCode"]},
            {"step": 2, "title": "Master Data Structures & Algorithms", "resources": ["NeetCode", "GeeksforGeeks"]},
            {"step": 3, "title": "Build Projects", "resources": ["GitHub", "Kaggle"]},
            {"step": 4, "title": "Apply for Internships", "resources": ["LinkedIn", "AngelList"]}
        ],
        "timeline": "6-12 months"
    }


def analyze_skill_gaps(career_goal, current_skills):
    """
    Mock logic for MVP — later this can be replaced with OpenAI API.
    """
    # Example pre-defined skills for simplicity
    required_skills_map = {
        "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "PostgreSQL"],
        "Data Scientist": ["Python", "Pandas", "NumPy", "Machine Learning", "SQL"],
        "Mobile App Developer": ["Kotlin", "Swift", "Flutter", "Firebase"],
    }

    required_skills = required_skills_map.get(career_goal, [])
    skill_gaps = [skill for skill in required_skills if skill not in current_skills]
    recommendations = [f"Learn {skill} via an online course or project" for skill in skill_gaps]

    return {
        "career_goal": career_goal,
        "required_skills": required_skills,
        "current_skills": current_skills,
        "skill_gaps": skill_gaps,
        "recommendations": recommendations,
    }


def build_roadmap_from_recommendation(rec_data, selected_career=None):
    """
    Build a roadmap structure from the AI career recommendation JSON.

    rec_data example:
    {
      "career_goal": "...",
      "recommendations": [
        {
          "career": "...",
          "reason": "...",
          "score": 95,
          "required_skills": [...]
        },
        ...
      ],
      "summary": "..."
    }

    selected_career: optional string, if provided we pick that career from the list.
    """
    if not rec_data:
        return {
            "message": "No recommendation data provided."
        }

    recommendations = rec_data.get("recommendations", [])
    if not isinstance(recommendations, list) or not recommendations:
        return {
            "message": "No recommendations list found in data."
        }

    chosen = None

    # 1) If user gave a selected career name, try to match it
    if selected_career:
        sel_lower = selected_career.strip().lower()
        for r in recommendations:
            if str(r.get("career", "")).strip().lower() == sel_lower:
                chosen = r
                break

    # 2) Fallback: if no chosen career found, pick highest score
    if chosen is None:
        chosen = sorted(
            recommendations,
            key=lambda r: r.get("score", 0),
            reverse=True
        )[0]

    career = chosen.get("career", "Unknown Career")
    required_skills = chosen.get("required_skills", [])
    summary = rec_data.get("summary", "")

    foundation_skills = required_skills[:2]
    core_skills = required_skills[2:4]
    advanced_skills = required_skills[4:]

    roadmap = {
        "target_career": career,
        "career_goal": rec_data.get("career_goal", ""),
        "summary": summary,
        "phases": [
            {
                "name": "Phase 1: Foundations",
                "duration_weeks": 4,
                "description": "Build strong fundamentals required for this career.",
                "skills": foundation_skills,
                "suggested_actions": [
                    "Follow a beginner course for these skills.",
                    "Take notes and make small practice exercises."
                ],
            },
            {
                "name": "Phase 2: Core Skills & Projects",
                "duration_weeks": 6,
                "description": "Work on the core skills that will be used in real-world projects.",
                "skills": core_skills,
                "suggested_actions": [
                    "Build 1–2 small projects using these skills.",
                    "Push your code to GitHub and document your learning."
                ],
            },
            {
                "name": "Phase 3: Advanced & Portfolio",
                "duration_weeks": 6,
                "description": "Move to advanced topics and create portfolio-ready projects.",
                "skills": advanced_skills,
                "suggested_actions": [
                    "Build at least one larger project that combines all skills.",
                    "Prepare a portfolio and resume tailored to this career."
                ],
            },
        ],
    }

    return roadmap


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
