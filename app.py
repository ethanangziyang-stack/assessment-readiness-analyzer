import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# -----------------------------
# App Title
# -----------------------------
st.title("Assessment Prioritizer")
st.write(
    "Prioritize subjects for revision based on scores, confidence, tuition support, and available time."
)

# -----------------------------
# Time Input Section
# -----------------------------
st.header("Daily Schedule Input")

leave_house_time = st.time_input(
    "Leave House Time",
    value=datetime.strptime("08:00", "%H:%M").time()
)

reach_home_time = st.time_input(
    "Reach Home Time",
    value=datetime.strptime("15:30", "%H:%M").time()
)

sleep_time = st.time_input(
    "Sleep Time",
    value=datetime.strptime("22:00", "%H:%M").time()
)

preferred_study_duration = st.number_input(
    "Preferred duration per study session (minutes)",
    min_value=15,
    max_value=180,
    step=15
)

# Calculate free time window
free_start = datetime.combine(datetime.today(), reach_home_time)
free_end = datetime.combine(datetime.today(), sleep_time)

if free_end <= free_start:
    st.error("Sleep time must be after reach home time.")
    free_slots = []
else:
    free_slots = [(free_start, free_end)]

# -----------------------------
# Subject Input Section
# -----------------------------
st.header("Subject Input")

num_subjects = st.number_input(
    "Number of subjects",
    min_value=1,
    max_value=10,
    step=1
)

subjects = []

for i in range(num_subjects):
    st.subheader(f"Subject {i + 1}")

    name = st.text_input("Subject name", key=f"name_{i}")
    score = st.number_input(
        "Current score (0–100)",
        0,
        100,
        50,
        key=f"score_{i}"
    )
    confidence = st.slider(
        "Confidence (1–5)",
        1,
        5,
        3,
        key=f"conf_{i}"
    )
    tuition = st.checkbox(
        "Do you have tuition for this subject?",
        key=f"tuition_{i}"
    )

    if name:
        subjects.append([name, score, confidence, tuition])

# -----------------------------
# Priority Calculation
# -----------------------------
if subjects:
    df = pd.DataFrame(
        subjects,
        columns=["Subject", "Score", "Confidence", "Tuition"]
    )

    # Tuition slightly reduces urgency (not dominant)
    df["Tuition Factor"] = df["Tuition"].apply(lambda x: 0.3 if x else 0)

    df["Priority Score"] = (
        (1 - df["Score"] / 100)
        * (6 - df["Confidence"])
        * (1 - df["Tuition Factor"])
    )

    df = df.sort_values(
        "Priority Score",
        ascending=False
    ).reset_index(drop=True)

    # -----------------------------
    # Display Results
    # -----------------------------
    st.subheader("Subject Priority Table")
    st.dataframe(
        df[["Subject", "Score", "Confidence", "Tuition", "Priority Score"]]
    )

    st.subheader("Priority Chart")
    st.bar_chart(df.set_index("Subject")["Priority Score"])

    # -----------------------------
    # Study Schedule Allocation
    # -----------------------------
    st.header("Suggested Study Schedule")

    study_sessions = []
    session_duration = timedelta(minutes=preferred_study_duration)
    current_time = free_start

    for _, row in df.iterrows():
        if current_time + session_duration > free_end:
            break

        study_sessions.append({
            "Subject": row["Subject"],
            "Start": current_time.strftime("%H:%M"),
            "End": (current_time + session_duration).strftime("%H:%M")
        })

        current_time += session_duration

    if study_sessions:
        st.dataframe(pd.DataFrame(study_sessions))
    else:
        st.info("No study sessions could be scheduled within your available free time.")

else:
    st.info("Enter at least one subject to calculate priority.")