# Importing libraries (Ethan Ang)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time

st.title("Assessment Prioritizer")
st.write(
    "This tool helps students prioritise revision subjects and plan study time "
    "while encouraging healthy routines aligned with Grow Well SG."
)

# Time Input (Lee Ren Jie)

st.header("Daily Schedule")

leave_house = st.time_input("Leave house time", time(8, 0))
reach_home = st.time_input("Reach home time", time(17, 0))
sleep_time = st.time_input("Sleep time", time(23, 0))

dinner_start = st.time_input("Dinner start time", time(19, 0))
dinner_end = st.time_input("Dinner end time", time(19, 45))

session_minutes = st.number_input(
    "Preferred study duration per session (minutes)",
    min_value=20,
    max_value=120,
    step=10
)


# Validate & normalise times (Ethan Ang)
today = datetime.today().date()
reach_dt = datetime.combine(today, reach_home)
sleep_dt = datetime.combine(today, sleep_time)

# Handle cross-midnight sleep
if sleep_dt <= reach_dt:
    sleep_dt += timedelta(days=1)

dinner_start_dt = datetime.combine(today, dinner_start)
dinner_end_dt = datetime.combine(today, dinner_end)
if dinner_end_dt <= dinner_start_dt:
    dinner_end_dt += timedelta(days=1)

# Sleep health warning
if sleep_dt.time() > time(0, 0):
    st.warning(
        "Your sleep time is quite late. Grow Well SG recommends consistent sleep "
        "before 10:30pm to support learning and wellbeing."
    )

# Subject Input
st.header("Subjects")

grade_map = {
    "A1": 0.05, "A2": 0.10,
    "B3": 0.25, "B4": 0.35,
    "C5": 0.50, "C6": 0.60,
    "D7": 0.75, "E8": 0.85,
    "F9": 1.00
}

num_subjects = st.number_input("Number of subjects", 1, 10, 1)
subjects = []

for i in range(num_subjects):
    st.subheader(f"Subject {i + 1}")

    name = st.text_input("Subject name", key=f"name_{i}")
    grade = st.selectbox(
        "Current grade",
        list(grade_map.keys()),
        key=f"grade_{i}"
    )
    confidence = st.slider(
        "Confidence (1 = least confident, 5 = most confident)",
        1, 5, 3,
        key=f"conf_{i}"
    )
    tuition = st.checkbox("Has tuition support", key=f"tuition_{i}")

    if name.strip():
        subjects.append([name, grade, confidence, tuition])

if not subjects:
    st.info("Please enter at least one subject.")
    st.stop()

df = pd.DataFrame(
    subjects,
    columns=["Subject", "Grade", "Confidence", "Tuition"]
)
# Priority Logic (fixed)
def calculate_priority(grade, confidence, tuition):
    grade_urgency = grade_map[grade]
    confidence_urgency = (5 - confidence) / 4

    base = (0.6 * grade_urgency) + (0.4 * confidence_urgency)
    modifier = 0.85 if tuition else 1.0

    return round(base * modifier, 3)

df["Priority Score"] = df.apply(
    lambda r: calculate_priority(
        r["Grade"], r["Confidence"], r["Tuition"]
    ),
    axis=1
)

df = df.sort_values("Priority Score", ascending=False).reset_index(drop=True)

# Display priorities
st.subheader("Subject Priority")
st.dataframe(df)

# Study Schedule (no overlap)
st.header("Suggested Study Schedule")

study_sessions = []
current_time = reach_dt
session_delta = timedelta(minutes=session_minutes)

for _, row in df.iterrows():
    if current_time >= sleep_dt:
        break

    # Skip dinner
    if dinner_start_dt <= current_time < dinner_end_dt:
        current_time = dinner_end_dt

    end_time = current_time + session_delta
    if end_time > sleep_dt:
        break

    study_sessions.append({
        "Subject": row["Subject"],
        "Start": current_time.strftime("%H:%M"),
        "End": end_time.strftime("%H:%M")
    })

    current_time = end_time

if study_sessions:
    st.dataframe(pd.DataFrame(study_sessions))
else:
    st.info("No study sessions could be scheduled within your available time.")