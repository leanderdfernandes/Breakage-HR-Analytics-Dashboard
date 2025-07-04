import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

# Initialize Faker for realistic data
fake = Faker()

# Define departments
departments = ["Engineering", "HR", "Marketing", "Sales", "Finance", "Operations"]

# Define managers for each department
managers = {
    "Engineering": ["Sarah Johnson", "Michael Chen", "David Rodriguez"],
    "HR": ["Jennifer Smith", "Robert Wilson", "Lisa Brown"],
    "Marketing": ["Amanda Davis", "Christopher Lee", "Michelle Garcia"],
    "Sales": ["Daniel Martinez", "Jessica Taylor", "Kevin Anderson"],
    "Finance": ["Rachel Thompson", "Steven White", "Nicole Clark"],
    "Operations": ["Matthew Lewis", "Ashley Hall", "Ryan Walker"]
}

# Define survey columns
survey_columns = [
    "Job_Embeddedness1", "Job_Embeddedness2", "Job_Embeddedness3", "Job_Embeddedness4",
    "Job_Embeddedness5", "Job_Embeddedness6", "Job_Embeddedness7",
    "POS1", "POS2", "POS3", "POS4", "POS5", "POS6", "POS7", "POS8", "POS9", "POS10",
    "Burnout_Exhaustion1", "Burnout_Exhaustion2", "Burnout_Exhaustion3", "Burnout_Exhaustion4",
    "Burnout_Disengagement1", "Burnout_Disengagement2", "Burnout_Disengagement3", "Burnout_Disengagement4",
    "Job_Satisfaction1", "Job_Satisfaction2", "Job_Satisfaction3",
    "Psych_Safety1", "Psych_Safety2", "Psych_Safety3", "Psych_Safety4", "Psych_Safety5", "Psych_Safety6", "Psych_Safety7",
    "UWES_Vigor1", "UWES_Vigor2", "UWES_Vigor3",
    "UWES_Dedication1", "UWES_Dedication2", "UWES_Dedication3",
    "UWES_Absorption1", "UWES_Absorption2", "UWES_Absorption3"
]

# Define possible complaints and suggestions
complaints = [
    "Lack of clear communication from management",
    "Limited opportunities for career advancement",
    "High workload during peak periods",
    "Insufficient team collaboration",
    "Lack of recognition for contributions",
    "Inadequate resources for projects",
    "Unclear performance expectations",
    "Limited work-from-home flexibility"
]

suggestions = [
    "Improve team meeting frequency and clarity",
    "Offer more professional development programs",
    "Better workload distribution during peak times",
    "Implement regular feedback sessions",
    "Enhance recognition programs for employees",
    "Provide more resources for project completion",
    "Clarify performance goals and metrics",
    "Expand flexible work arrangements"
]

# Generate data
n_employees = 100
data = {
    "EmployeeID": [f"EMP{str(i+1).zfill(3)}" for i in range(n_employees)],
    "Name": [fake.name() for _ in range(n_employees)],
    "Department": [random.choice(departments) for _ in range(n_employees)],
}

# Add missing fields
data["Age"] = np.random.randint(22, 65, n_employees)
data["Tenure_Years"] = np.random.randint(0, 15, n_employees)
data["Tenure_Months"] = np.random.randint(0, 12, n_employees)
data["Recent_Promotion"] = [random.choice(["Yes", "No"]) for _ in range(n_employees)]
data["Employment_Type"] = [random.choice(["Full Time", "Part Time"]) for _ in range(n_employees)]

# Add managers based on department
data["Manager"] = [random.choice(managers[dept]) for dept in data["Department"]]

# Add survey responses (1-5, normal distribution around mean 3, std 1)
for col in survey_columns:
    data[col] = np.clip(np.random.normal(loc=3, scale=1, size=n_employees).round(), 1, 5).astype(int)

# Add complaints and suggestions (80% chance of having a value)
data["Complaints"] = [random.choice(complaints) if random.random() < 0.8 else "" for _ in range(n_employees)]
data["Improvements_Suggestions"] = [random.choice(suggestions) if random.random() < 0.8 else "" for _ in range(n_employees)]

# Create DataFrame and save to CSV
df = pd.DataFrame(data)
df.to_csv("employee_data_enhanced.csv", index=False)

print("Generated employee_data_enhanced.csv with 100 employee records including all required fields.") 