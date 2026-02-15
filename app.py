import streamlit as st
import pandas as pd
from datetime import date

st.title("📊 Assessment Readiness Analyzer")

st.write(
    "This application helps students evaluate how prepared they are "
    "for an upcoming assessment based on time left and confidence levels."
)

assessment_date = st.date_input(
    "Assessment date",
    min_value=date.today()
)

days_left = (assessment_date - date.today()).days

if days_left <= 3:
    urgency_weight = 1.0
elif days_left <= 7:
    urgency_weight = 0.8
elif days_left <= 14:
    urgency_weight = 0.6
else:
    urgency_weight = 0.4

st.subheader("📚 Topic Confidence Input")

num_topics = st.number_input(
    "Number of topics",
    min_value=1,
    max_value=10,
    step=1
)

topics = []

for i in range(int(num_topics)):
    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input(f"Topic {i+1}")
    with col2:
        confidence = st.slider(
            "Confidence (1–5)",
            1, 5, 3,
            key=f"conf_{i}"
        )

    if topic:
        topics.append([topic, confidence])

if topics:
    df = pd.DataFrame(topics, columns=["Topic", "Confidence"])
    df["Readiness Score"] = (df["Confidence"] / 5) * urgency_weight * 100

    overall_readiness = df["Readiness Score"].mean()

    st.subheader("📈 Results")
    st.dataframe(df)

    st.metric("Overall Readiness (%)", f"{overall_readiness:.1f}")

    if overall_readiness >= 75:
        st.success("Low Risk – You are well prepared.")
    elif overall_readiness >= 50:
        st.warning("Medium Risk – Focus on weaker topics.")
    else:
        st.error("High Risk – Immediate revision recommended.")

    st.bar_chart(df.set_index("Topic")["Readiness Score"])
