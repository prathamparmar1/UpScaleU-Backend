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
