import streamlit as st
import json
import time
import os
import re
import random

from services.llm_service import generate_questions, fallback_response
from utils.validators import validate_email, validate_phone, validate_experience
from utils.data_handler import save_candidate, mask_phone

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


st.set_page_config(page_title="TalentScout Hiring Assistant")
st.title("🤖 TalentScout Hiring Assistant")

# ---------------- SESSION STATE ----------------

if "stage" not in st.session_state:
    st.session_state.stage = "greeting"
    st.session_state.candidate = {}
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.current_question_index = 0
    st.session_state.question_start_time = None
    st.session_state.chat_history = []

# ---------------- SAVE INTERVIEW ----------------

def save_full_interview():

    record = {
        "candidate": st.session_state.candidate,
        "answers": st.session_state.answers,
        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    file_name = "interview_records.json"

    if not os.path.exists(file_name) or os.path.getsize(file_name) == 0:
        with open(file_name, "w") as f:
            json.dump([], f)

    with open(file_name, "r") as f:
        try:
            data = json.load(f)
        except:
            data = []

    data.append(record)

    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- PDF ----------------

def generate_pdf_report():

    file_path = "Interview_Report.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("TalentScout Interview Report", styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("<b>Candidate Information:</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    for key, value in st.session_state.candidate.items():
        elements.append(Paragraph(f"{key.capitalize()}: {value}", styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))

    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("<b>Interview Responses:</b>", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    for i, qa in enumerate(st.session_state.answers):
        elements.append(Paragraph(f"<b>Q{i+1}:</b> {qa['question']}", styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>Answer:</b> {qa['answer']}", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    return file_path

# ---------------- END INTERVIEW ----------------

def end_conversation():
    save_full_interview()
    st.session_state.stage = "ended"

# ---------------- GREETING ----------------

if st.session_state.stage == "greeting":

    st.write("Hello! I'm TalentScout Hiring Assistant.")

    if st.button("Start Interview"):
        st.session_state.stage = "collect_info"
        st.rerun()

# ---------------- COLLECT INFO ----------------

elif st.session_state.stage == "collect_info":

    with st.form("form"):

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone (10 digits)")
        experience = st.text_input("Years of Experience")
        location = st.text_input("Location")
        position = st.text_input("Desired Position")
        tech_stack = st.text_input("Tech Stack (comma separated)")

        submitted = st.form_submit_button("Submit")

        if submitted:

            valid = True

            if not validate_email(email):
                st.error("Invalid Email")
                valid = False

            if not validate_phone(phone):
                st.error("Phone must be 10 digits")
                valid = False

            if not validate_experience(experience):
                st.error("Invalid Experience")
                valid = False

            if valid:

                st.session_state.candidate = {
                    "name": name,
                    "email": email,
                    "phone": mask_phone(phone),
                    "experience": experience,
                    "location": location,
                    "position": position,
                    "tech_stack": [t.strip() for t in tech_stack.split(",")]
                }

                save_candidate(st.session_state.candidate)

                st.session_state.stage = "generate"
                st.rerun()

# ---------------- GENERATE QUESTIONS ----------------

elif st.session_state.stage == "generate":

    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.current_question_index = 0

    for tech in st.session_state.candidate["tech_stack"]:

        response = generate_questions(
            tech,
            st.session_state.candidate["experience"]
        )

        try:
            clean_response = response.strip().replace("```json", "").replace("```", "")
            parsed = json.loads(clean_response)

            if "questions" in parsed and isinstance(parsed["questions"], list):
                st.session_state.questions.extend(parsed["questions"])

        except:
            pass

    # Ensure exactly 10 questions
    st.session_state.questions = st.session_state.questions[:10]

    while len(st.session_state.questions) < 10:
        st.session_state.questions.append(
            f"Explain a beginner to medium level concept in {st.session_state.candidate['tech_stack'][0]}."
        )

    random.shuffle(st.session_state.questions)

    st.session_state.stage = "interview"
    st.session_state.question_start_time = time.time()
    st.rerun()

# ---------------- INTERVIEW ----------------

elif st.session_state.stage == "interview":

    index = st.session_state.current_question_index

    if index < 10:

        question = st.session_state.questions[index]

        st.subheader(f"Question {index+1} of 10")
        st.write(question)

        TOTAL_TIME = 150  # 2 minutes 30 seconds

        elapsed = int(time.time() - st.session_state.question_start_time)
        remaining = TOTAL_TIME - elapsed

        if remaining <= 0:

            st.session_state.answers.append({
                "question": question,
                "answer": "No Answer (Time Expired)"
            })

            st.session_state.current_question_index += 1
            st.session_state.question_start_time = time.time()
            st.rerun()

        else:
            minutes = remaining // 60
            seconds = remaining % 60
            st.warning(f"⏳ Time Remaining: {minutes}:{seconds:02d}")

        answer = st.text_area("Your Answer", key=f"answer_{index}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Next"):
                ans = st.session_state.get(f"answer_{index}", "")
                st.session_state.answers.append({
                    "question": question,
                    "answer": ans
                })
                st.session_state.current_question_index += 1
                st.session_state.question_start_time = time.time()
                st.rerun()

        with col2:
            if st.button("Exit Interview"):
                end_conversation()
                st.rerun()

        time.sleep(1)
        st.rerun()

    else:
        end_conversation()
        st.rerun()

# ---------------- ENDED ----------------

elif st.session_state.stage == "ended":

    st.markdown("""
        <div style='text-align:center; margin-top:60px;'>
        <h1>🎉 Interview Completed</h1>
        <h4>You may ask about interview question numbers only.</h4>
        </div>
    """, unsafe_allow_html=True)

    pdf_file = generate_pdf_report()

    with open(pdf_file, "rb") as f:
        st.download_button("Download Interview Report", f, file_name="Interview_Report.pdf")

    if st.button("Exit Portal"):
        st.session_state.stage = "closed"
        st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about interview question numbers only")

    if user_input:

        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("⏳ Generating answer...")

            match = re.search(r'(\d+)', user_input)

            if match:
                q_index = int(match.group(1)) - 1

                if 0 <= q_index < len(st.session_state.questions):
                    question_text = st.session_state.questions[q_index]

                    prompt = f"""
                    Provide a short, clean, professional model answer only.
                    Beginner to Medium level.
                    No JSON.
                    No extra explanation.
                    Question: {question_text}
                    """

                    response = fallback_response(prompt)
                    clean_response = response.strip().replace("```", "")

                    final_output = f"""
**Question {q_index+1}:**
{question_text}

**Model Answer:**
{clean_response}
"""
                else:
                    final_output = "❌ Invalid question number."
            else:
                final_output = "⚠ Please ask using question number only."

            placeholder.markdown(final_output)

        st.session_state.chat_history.append({"role": "assistant", "content": final_output})
        st.rerun()

# ---------------- CLOSED ----------------

elif st.session_state.stage == "closed":

    st.markdown("""
        <div style='text-align:center; margin-top:120px;'>
        <h1>✅ Session Closed</h1>
        <h2>Thank you for using TalentScout Hiring Assistant.</h2>
        </div>
    """, unsafe_allow_html=True)