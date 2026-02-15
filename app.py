# app.py
import streamlit as st
import pandas as pd
from datetime import date
import firebase_admin
from firebase_admin import credentials, firestore

# ------------------------
# Firebase Initialization
# ------------------------
# Replace with path to your Firebase service account JSON
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
# Subject Input Section
# ------------------------
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

    if name:
        subjects.append([name, score, confidence, tuition])

# ------------------------
# Priority Calculation
# ------------------------
if subjects:
    df = pd.DataFrame(subjects, columns=["Subject", "Score", "Confidence", "Tuition"])

    # Tuition factor: reduces priority if tuition exists
    df["Tuition Factor"] = df["Tuition"].apply(lambda x: 0.3 if x else 0)

    # Priority formula: higher value = more urgent
    df["Priority Score"] = (1 - df["Score"]/100) * (6 - df["Confidence"]) * (1 - df["Tuition Factor"])

    # Sort descending: most urgent first
    df = df.sort_values("Priority Score", ascending=False).reset_index(drop=True)

    # ------------------------
    # Display Results
    # ------------------------
    st.subheader("📈 Subject Priority Table")
    st.dataframe(df[["Subject", "Score", "Confidence", "Tuition", "Priority Score"]])

    st.subheader("📊 Priority Chart")
    st.bar_chart(df.set_index("Subject")["Priority Score"])

    # ------------------------
    # Save to Firebase
    # ------------------------
    if FIREBASE_READY:
        if st.button("💾 Save Report to Firebase"):
            try:
                # Convert DataFrame to dict
                report_data = df.to_dict(orient="records")
                # Add timestamp
                report_doc = {
                    "date": date.today().isoformat(),
                    "report": report_data
                }
                db.collection("revision_reports").add(report_doc)
                st.success("Report saved to Firebase! You can trigger email notifications from Cloud Functions.")
            except Exception as e:
                st.error(f"Error saving to Firebase: {e}")
else:
    st.info("Enter at least one subject to calculate priority.")
