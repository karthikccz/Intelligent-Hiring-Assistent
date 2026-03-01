import os
import random
import google.generativeai as genai
from dotenv import load_dotenv
from services.prompt_templates import SYSTEM_PROMPT

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-3-flash-preview")


def generate_questions(technology, experience):

    random_seed = random.randint(1, 999999)

    prompt = f"""
{SYSTEM_PROMPT}

You are a technical interviewer.

Technology: {technology}
Candidate Experience: {experience} years

Instructions:
- Generate EXACTLY 10 UNIQUE technical interview questions.
- Difficulty level: Beginner to Medium ONLY.
- Do NOT generate advanced, system design, or expert-level questions.
- Focus on fundamentals, practical coding, real-world basics.
- Questions must be different each time.
- Avoid repetition.
- Avoid very basic definition-only questions.
- Mix conceptual + small practical thinking questions.

Random seed: {random_seed}

Return ONLY valid JSON in this format:

{{
  "questions": [
    "Question 1",
    "Question 2",
    ...
    "Question 10"
  ]
}}
"""

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40
        }
    )

    return response.text


def fallback_response(user_input):

    prompt = f"""
{SYSTEM_PROMPT}

User Query: {user_input}

Rules:
- Only answer if related to interview questions.
- Keep answer beginner to medium level.
- Short, clean, professional.
- No JSON.
- No extra explanation.
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.5}
    )

    return response.text.strip().replace("```", "")