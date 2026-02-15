# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# ------------------------
# Firebase Initialization
# ------------------------
FIREBASE_CRED_PATH = "serviceAccountKey.json"

try:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    FIREBASE_READY = True
except Exception as e:
    st.warning("Firebase not initialized. Email sync will not work.")
    FIREBASE_READY = False

# ------------------------
# App Title
# ------------------------
st.title("📊 Enhanced Assessment Prioritizer")
st.write(
    "Prioritize subjects for revision based on scores, confidence, and tuition support."
)

# ------------------------
# Daily Schedule & Study Preferences
# ------------------------
st.header("🗓️ Daily Schedule & Study Preferences")

breakfast = st.time_input("Breakfast time", key="breakfast")
lunch = st.time_input("Lunch time", key="lunch")
dinner = st.time_input("Dinner time", key="dinner")

school_start = st.time_input("School start time", key="school_start")
school_end = st.time_input("School end time", key="school_end")

free_start = st.time_input("Free time start", key="free_start")
free_end = st.time_input("Free time end", key="free_end")

study_duration = st.number_input(
    "Preferred study duration per session (minutes)", min_value=15, max_value=180, step=15, value=60
)

# ------------------------
# Subject Input Section
# ------------------------
st.header("📚 Subjects & Priorities")

num_subjects = st.number_input(
    "Number of subjects", min_value=1, max_value=10, step=1
)

subjects = []
for i in range(num_subjects):
    st.subheader(f"Subject {i+1}")
    name = st.text_input("Subject name", key=f"name_{i}")
    score = st.number_input("Current score (0-100)", 0, 100, 50, key=f"score_{i}")
    confidence = st.slider("Confidence (1-5)", 1, 5, 3, key=f"conf_{i}")
    tuition = st.checkbox("Do you have tuition for this subject?", key=f"tuition_{i}")
    sessions = st.number_input(
        "Number of study sessions for this subject",
        min_value=1,
        max_value=10,
        step=1,
        value=1,
        key=f"sessions_{i}"
    )
    if name:
        subjects.append([name, score, confidence, tuition, sessions])

# ------------------------
# Priority Calculation
# ------------------------
if subjects:
    df = pd.DataFrame(subjects, columns=["Subject", "Score", "Confidence", "Tuition", "Sessions"])
    df["Tuition Factor"] = df["Tuition"].apply(lambda x: 0.3 if x else 0)
    df["Priority Score"] = (1 - df["Score"]/100) * (6 - df["Confidence"]) * (1 - df["Tuition Factor"])
    df = df.sort_values("Priority Score", ascending=False).reset_index(drop=True)

    st.subheader("📈 Subject Priority Table")
    st.dataframe(df[["Subject", "Score", "Confidence", "Tuition", "Priority Score", "Sessions"]])

    st.subheader("📊 Priority Chart")
    st.bar_chart(df.set_index("Subject")["Priority Score"])

    # ------------------------
    # Generate Study Slots
    # ------------------------
    st.header("🗓️ Generated Study Timetable")

    def generate_study_slots(free_start, free_end, meals, school, duration_min):
        slots = []
        current_time = datetime.combine(date.today(), free_start)
        free_end_dt = datetime.combine(date.today(), free_end)
        meal_periods = [(datetime.combine(date.today(), t), datetime.combine(date.today(), t) + timedelta(minutes=30)) for t in meals]
        school_period = (datetime.combine(date.today(), school[0]), datetime.combine(date.today(), school[1]))
        while current_time + timedelta(minutes=duration_min) <= free_end_dt:
            session_end = current_time + timedelta(minutes=duration_min)
            overlap_meal = any(current_time < m_end and session_end > m_start for m_start, m_end in meal_periods)
            overlap_school = current_time < school_period[1] and session_end > school_period[0]
            if not overlap_meal and not overlap_school:
                slots.append((current_time, session_end))
            current_time += timedelta(minutes=duration_min)
        return slots

    meals = [breakfast, lunch, dinner]
    school = [school_start, school_end]
    study_slots = generate_study_slots(free_start, free_end, meals, school, study_duration)

    if not study_slots:
        st.info("No study slots available in the given free time avoiding meals and school.")
    else:
        # Allocate slots to subjects proportionally to priority & sessions
        allocated_slots = []
        slot_index = 0
        total_sessions = df["Sessions"].sum()
        for _, row in df.iterrows():
            for _ in range(row["Sessions"]):
                if slot_index >= len(study_slots):
                    break
                start, end = study_slots[slot_index]
                allocated_slots.append({
                    "Subject": row["Subject"],
                    "Time": f"{start.time().strftime('%H:%M')} - {end.time().strftime('%H:%M')}"
                })
                slot_index += 1

        timetable_df = pd.DataFrame(allocated_slots)
        st.dataframe(timetable_df)

    # ------------------------
    # Save to Firebase
    # ------------------------
    if FIREBASE_READY:
        if st.button("💾 Save Report to Firebase"):
            try:
                report_data = df.to_dict(orient="records")
                timetable_data = timetable_df.to_dict(orient="records") if study_slots else []
                report_doc = {
                    "date": date.today().isoformat(),
                    "report": report_data,
                    "timetable": timetable_data
                }
                db.collection("revision_reports").add(report_doc)
                st.success("Report saved to Firebase! You can trigger email notifications from Cloud Functions.")
            except Exception as e:
                st.error(f"Error saving to Firebase: {e}")
else:
    st.info("Enter at least one subject to calculate priority.")
