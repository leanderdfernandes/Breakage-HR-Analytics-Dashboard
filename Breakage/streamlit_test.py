import streamlit as st
import pandas as pd
import numpy as np
from fuzzywuzzy import process
from datetime import datetime
import logging
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if CSV file exists
if not os.path.exists("employee_data.csv"):
    st.error("Error: employee_data.csv not found in the current directory.")
    st.stop()

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("employee_data.csv")
        logger.info("Successfully loaded employee_data.csv")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        st.error(f"Error loading CSV: {e}")
        st.stop()

df = load_data()

# Load LLM and tokenizer
@st.cache_resource
def load_llm():
    try:
        model_name = "tiiuae/falcon-7b-instruct"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        logger.info(f"Successfully loaded LLM and tokenizer on {device}")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Failed to load LLM: {e}")
        return None, None

model, tokenizer = load_llm()

# Survey question groups
question_groups = {
    "Job Embeddedness": [
        "Job_Embeddedness1", "Job_Embeddedness2", "Job_Embeddedness3", "Job_Embeddedness4",
        "Job_Embeddedness5", "Job_Embeddedness6", "Job_Embeddedness7"
    ],
    "Perceived Organizational Support": [
        "POS1", "POS2", "POS3", "POS4", "POS5", "POS6", "POS7", "POS8", "POS9", "POS10"
    ],
    "Burnout Exhaustion": [
        "Burnout_Exhaustion1", "Burnout_Exhaustion2", "Burnout_Exhaustion3", "Burnout_Exhaustion4"
    ],
    "Burnout Disengagement": [
        "Burnout_Disengagement1", "Burnout_Disengagement2", "Burnout_Disengagement3", "Burnout_Disengagement4"
    ],
    "Job Satisfaction": [
        "Job_Satisfaction1", "Job_Satisfaction2", "Job_Satisfaction3"
    ],
    "Psychological Safety": [
        "Psych_Safety1", "Psych_Safety2", "Psych_Safety3", "Psych_Safety4",
        "Psych_Safety5", "Psych_Safety6", "Psych_Safety7"
    ],
    "UWES Vigor": [
        "UWES_Vigor1", "UWES_Vigor2", "UWES_Vigor3"
    ],
    "UWES Dedication": [
        "UWES_Dedication1", "UWES_Dedication2", "UWES_Dedication3"
    ],
    "UWES Absorption": [
        "UWES_Absorption1", "UWES_Absorption2", "UWES_Absorption3"
    ]
}

# Reverse-scored questions
reverse_scored = [
    "Job_Embeddedness6", "Burnout_Exhaustion3", "Burnout_Disengagement1",
    "Burnout_Disengagement3", "Burnout_Disengagement4", "Psych_Safety1",
    "Psych_Safety3", "Psych_Safety5"
]

# Function to calculate scores
def calculate_scores(row):
    scores = {}
    for group, cols in question_groups.items():
        group_data = row[cols].copy()
        for col in cols:
            if col in reverse_scored:
                group_data[col] = 6 - group_data[col]
        scores[group] = np.nanmean(group_data) * 2 if not group_data.isna().all() else np.nan
    burnout_score = np.nanmean([scores.get("Burnout Exhaustion", np.nan), scores.get("Burnout Disengagement", np.nan)])
    scores["Burnout"] = burnout_score if not np.isnan(burnout_score) else np.nan
    uwes_score = np.nanmean([scores.get("UWES Vigor", np.nan), scores.get("UWES Dedication", np.nan), scores.get("UWES Absorption", np.nan)])
    scores["UWES"] = uwes_score if not np.isnan(uwes_score) else np.nan
    return scores

# Function to calculate attrition score
def calculate_attrition_score(scores):
    weights = {
        "Job Embeddedness": 0.2,
        "Perceived Organizational Support": 0.2,
        "Burnout": 0.3,
        "Job Satisfaction": 0.2,
        "Psychological Safety": 0.15,
        "UWES": 0.15
    }
    available = {k: v for k, v in scores.items() if not np.isnan(v)}
    total_weight = sum(weights[k] for k in available if k in weights)
    if total_weight == 0:
        return np.nan
    adjusted_weights = {k: w / total_weight for k, w in weights.items() if k in available}
    attrition = 0
    for group in adjusted_weights:
        score = scores.get(group, np.nan)
        if not np.isnan(score):
            if group == "Burnout":
                attrition += adjusted_weights[group] * score
            else:
                attrition += adjusted_weights[group] * (10 - score)
    return min(attrition * 10, 100)

# Function to generate LLM summary
def generate_summary(scores, attrition_score, complaints, suggestions):
    if model is None or tokenizer is None:
        return "Error: LLM not available."
    try:
        survey_scores_str = ", ".join([
            f"{k}: {v:.2f}" if not np.isnan(v) else f"{k}: Not Available"
            for k, v in scores.items() if k not in ["Burnout Exhaustion", "Burnout Disengagement", "UWES Vigor", "UWES Dedication", "UWES Absorption"]
        ])
        system_prompt = (
            "You are an expert HR advisor. Given the following employee survey scores (0-10), attrition risk (0-100), complaints, and suggestions, "
            "write a concise, professional summary (150-200 words) of the employee's engagement and well-being. "
            "Highlight strengths and concerns, and provide 2-3 specific, actionable strategies to retain or mentor this employee. "
            "Be empathetic, clear, and practical."
        )
        user_prompt = (
            f"Survey Scores: {survey_scores_str}\n"
            f"Attrition Risk: {attrition_score:.2f}\n"
            f"Complaints: {complaints or 'None'}\n"
            f"Suggestions: {suggestions or 'None'}\n"
        )
        prompt = system_prompt + "\n" + user_prompt
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        outputs = model.generate(**inputs, max_length=300, num_return_sequences=1, temperature=0.7, do_sample=True)
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary.split(user_prompt)[-1].strip() if user_prompt in summary else summary.strip()
    except Exception as e:
        logger.error(f"Failed to generate LLM summary: {e}")
        return f"Error generating summary: {e}"

# Streamlit UI
st.title("HR Employee Metrics Dashboard")
logger.info("Streamlit app started. Access at http://localhost:8501")

# Name search with autocomplete
name_input = st.text_input("Search Employee by Name", "")
if name_input:
    suggestions = process.extract(name_input, df["Name"], limit=5)
    suggested_names = [s[0] for s in suggestions]
    selected_name = st.selectbox("Select Employee", suggested_names, index=0)
else:
    selected_name = st.selectbox("Select Employee", df["Name"])

# Filter data for selected employee
employee_data = df[df["Name"] == selected_name]
if not employee_data.empty:
    row = employee_data.iloc[0]
    st.subheader(f"Metrics for {selected_name}")
    st.write(f"Employee ID: {row['EmployeeID']}")
    st.write(f"Department: {row['Department']}")
    
    # Calculate and display scores
    scores = calculate_scores(row)
    st.subheader("Survey Scores (0-10)")
    for group, score in scores.items():
        if group not in ["Burnout Exhaustion", "Burnout Disengagement", "UWES Vigor", "UWES Dedication", "UWES Absorption"]:
            if not np.isnan(score):
                st.write(f"{group}: {score:.2f}/10")
            else:
                st.write(f"{group}: Not Available")
    
    # Calculate and display attrition score
    attrition_score = calculate_attrition_score(scores)
    st.subheader("Attrition Risk")
    if not np.isnan(attrition_score):
        st.write(f"Attrition Score: {attrition_score:.2f}/100")
        st.progress(min(attrition_score / 100, 1.0))
    else:
        st.write("Attrition Score: Not Available (insufficient data)")
    
    # Display complaints and suggestions
    st.subheader("Feedback")
    st.write(f"Complaints: {row['Complaints'] or 'None'}")
    st.write(f"Improvements Suggestions: {row['Improvements_Suggestions'] or 'None'}")
    
    # Generate and display LLM summary
    st.subheader("Employee Summary and Retention Strategies")
    if st.button("Generate Summary"):
        with st.spinner("Generating summary..."):
            summary = generate_summary(scores, attrition_score, row['Complaints'], row['Improvements_Suggestions'])
            st.write(summary)
else:
    st.error("Employee not found.")