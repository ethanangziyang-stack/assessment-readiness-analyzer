# app.py
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Initialization
FIREBASE_CRED_PATH = "serviceAccountKey.json"

try:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    FIREBASE_READY = True
except Exception:
    st.warning("Firebase not initialized. Email sync will not work.")
    FIREBASE_READY = False

# App Title
st.title("Enhanced Assessment Prioritizer")
st.write("Prioritize subjects for revision based on scores, confidence, tuition support, and available time.")

# Time Input Section
st.header("Daily Schedule Input")
leave_house_time = st.time_input("Leave House Time", value=datetime.strptime("08:00", "%H:%M").time())
reach_home_time = st.time_input("Reach Home Time", value=datetime.strptime("15:30", "%H:%M").time())
sleep_time = st.time_input("Sleep Time", value=datetime.strptime("22:00", "%H:%M").time())

preferred_study_duration = st.number_input(
    "Preferred duration per study session (minutes)", min_value=15, max_value=180, step=15
)

# Calculate free time (Reach Home -> Sleep)
free_start = datetime.combine(datetime.today(), reach_home_time)
free_end = datetime.combine(datetime.today(), sleep_time)
if free_end <= free_start:
    st.error("Sleep time must be after reach home time.")
    free_slots = []
else:
    free_slots = [(free_start, free_end)]

# Subject Input Section
st.header("Subject Input")
num_subjects = st.number_input("Number of subjects", min_value=1, max_value=10, step=1)
subjects = []

for i in range(num_subjects):
    st.subheader(f"Subject {i+1}")
    name = st.text_input("Subject name", key=f"name_{i}")
    score = st.number_input("Current score (0-100)", 0, 100, 50, key=f"score_{i}")
    confidence = st.slider("Confidence (1-5)", 1, 5, 3, key=f"conf_{i}")
    tuition = st.checkbox("Do you have tuition for this subject?", key=f"tuition_{i}")

    if name:
        subjects.append([name, score, confidence, tuition])

# Priority Calculation
if subjects:
    df = pd.DataFrame(subjects, columns=["Subject", "Score", "Confidence", "Tuition"])
    df["Tuition Factor"] = df["Tuition"].apply(lambda x: 0.3 if x else 0)
    df["Priority Score"] = (1 - df["Score"]/100) * (6 - df["Confidence"]) * (1 - df["Tuition Factor"])
    df = df.sort_values("Priority Score", ascending=False).reset_index(drop=True)

    # Display Results
    st.subheader("Subject Priority Table")
    st.dataframe(df[["Subject", "Score", "Confidence", "Tuition", "Priority Score"]])
    st.subheader("Priority Chart")
    st.bar_chart(df.set_index("Subject")["Priority Score"])

    # Allocate Study Sessions
    st.header("Suggested Study Schedule")
    study_sessions = []
    session_duration = timedelta(minutes=preferred_study_duration)
    for _, row in df.iterrows():
        subject_name = row["Subject"]
        current_time = free_start
        while current_time + session_duration <= free_end:
            study_sessions.append({
                "Subject": subject_name,
                "Start": current_time.strftime("%H:%M"),
                "End": (current_time + session_duration).strftime("%H:%M")
            })
            current_time += session_duration

    if study_sessions:
        st.dataframe(pd.DataFrame(study_sessions))
    else:
        st.info("No study sessions could be scheduled within your available free time.")

    # Save to Firebase
    if FIREBASE_READY and st.button("Save Report to Firebase"):
        try:
            report_data = df.to_dict(orient="records")
            report_doc = {
                "date": date.today().isoformat(),
                "report": report_data,
                "schedule": study_sessions
            }
            db.collection("revision_reports").add(report_doc)
            st.success("Report saved to Firebase! Email notifications can be triggered separately.")
        except Exception as e:
            st.error(f"Error saving to Firebase: {e}")
else:
    st.info("Enter at least one subject to calculate priority.")
