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
