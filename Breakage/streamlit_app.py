import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import base64
from datetime import datetime
from google import genai
import os
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Breakage - Attrition Risk Detector",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .risk-low {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    .risk-moderate {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    
    .risk-high {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    .department-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .employee-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 0.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .download-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
</style>
""", unsafe_allow_html=True)

# Google Gemini API configuration
GEMINI_API_KEY = "AIzaSyCnpRCQlbUnmEmPC77_P-gYXX2qG8eiTg4"
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

# Model definitions
MODEL_DEFS = {
    'job_embeddedness': {
        'name': 'Job Embeddedness',
        'author': 'Crossley et al., 2007',
        'description': 'Measures how embedded an employee is in their job and organization',
        'csv_columns': ['Job_Embeddedness1', 'Job_Embeddedness2', 'Job_Embeddedness3', 'Job_Embeddedness4', 'Job_Embeddedness5', 'Job_Embeddedness6', 'Job_Embeddedness7']
    },
    'perceived_organizational_support': {
        'name': 'Perceived Organizational Support',
        'author': 'Eisenberger et al., 1986',
        'description': 'Employee perception of organizational support and care',
        'csv_columns': ['POS1', 'POS2', 'POS3', 'POS4', 'POS5', 'POS6', 'POS7', 'POS8', 'POS9', 'POS10']
    },
    'burnout_olbi': {
        'name': 'Burnout (OLBI)',
        'author': 'Demerouti et al., 2001',
        'description': 'Measures emotional exhaustion and disengagement',
        'csv_columns': ['Burnout_Exhaustion1', 'Burnout_Exhaustion2', 'Burnout_Exhaustion3', 'Burnout_Exhaustion4', 'Burnout_Disengagement1', 'Burnout_Disengagement2', 'Burnout_Disengagement3', 'Burnout_Disengagement4']
    },
    'job_satisfaction_moaq': {
        'name': 'Job Satisfaction (MOAQ)',
        'author': 'Cammann et al., 1983',
        'description': 'Overall job satisfaction and contentment',
        'csv_columns': ['Job_Satisfaction1', 'Job_Satisfaction2', 'Job_Satisfaction3']
    },
    'psychological_safety': {
        'name': 'Psychological Safety',
        'author': 'Edmondson, 1999',
        'description': 'Perceived safety for interpersonal risk-taking',
        'csv_columns': ['Psych_Safety1', 'Psych_Safety2', 'Psych_Safety3', 'Psych_Safety4', 'Psych_Safety5', 'Psych_Safety6', 'Psych_Safety7']
    },
    'work_engagement': {
        'name': 'Work Engagement (UWES-9)',
        'author': 'Schaufeli et al., 2006',
        'description': 'Vigor, dedication, and absorption in work',
        'csv_columns': ['UWES_Vigor1', 'UWES_Vigor2', 'UWES_Vigor3', 'UWES_Dedication1', 'UWES_Dedication2', 'UWES_Dedication3', 'UWES_Absorption1', 'UWES_Absorption2', 'UWES_Absorption3']
    }
}

# Color palette
COLORS = {
    'primary': '#3b82f6',
    'secondary': '#8b5cf6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#06b6d4',
    'light': '#f8fafc',
    'dark': '#1f2937'
}

DEPARTMENT_COLORS = {
    'Sales': '#3b82f6',
    'Marketing': '#8b5cf6',
    'Engineering': '#10b981',
    'HR': '#f59e0b',
    'Finance': '#ef4444',
    'Operations': '#06b6d4',
    'IT': '#84cc16',
    'Legal': '#f97316'
}

@st.cache_data
def load_data():
    """Load and process employee data"""
    try:
        # Try enhanced CSV first, fall back to original
        try:
            df = pd.read_csv("employee_data_enhanced.csv")
        except FileNotFoundError:
            df = pd.read_csv("employee_data.csv")
            # Add missing columns with realistic values
            df['Age'] = np.random.randint(22, 65, len(df))
            df['Tenure_Years'] = np.random.randint(0, 15, len(df))
            df['Tenure_Months'] = np.random.randint(0, 12, len(df))
            df['Recent_Promotion'] = np.random.choice(["Yes", "No"], len(df))
            df['Employment_Type'] = np.random.choice(["Full Time", "Part Time"], len(df))
            df['Manager'] = "Manager " + np.random.randint(1, 10, len(df)).astype(str)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def calculate_psychometric_scores(df):
    """Calculate psychometric scores for all employees"""
    scores = {}
    
    for _, row in df.iterrows():
        emp_id = row['EmployeeID']
        emp_scores = {}
        
        for model_key, model_def in MODEL_DEFS.items():
            if 'csv_columns' in model_def:
                columns = model_def['csv_columns']
                values = [row[col] for col in columns if col in row and pd.notna(row[col])]
                if values:
                    avg_score = np.mean(values)
                    emp_scores[model_key] = round(avg_score, 2)
        
        scores[emp_id] = emp_scores
    
    return scores

def calculate_attrition_score(scores):
    """Calculate overall attrition risk score (0-100)"""
    if not scores:
        return 50
    
    # Weights for different factors
    weights = {
        'job_embeddedness': 0.25,
        'perceived_organizational_support': 0.20,
        'burnout_olbi': 0.25,
        'job_satisfaction_moaq': 0.20,
        'psychological_safety': 0.05,
        'work_engagement': 0.05
    }
    
    total_score = 0
    total_weight = 0
    
    for model, score in scores.items():
        if model in weights:
            # Invert scores for positive constructs
            if model in ['job_embeddedness', 'perceived_organizational_support', 'job_satisfaction_moaq', 'psychological_safety', 'work_engagement']:
                adjusted_score = 6 - score
            else:
                adjusted_score = score
            
            total_score += adjusted_score * weights[model]
            total_weight += weights[model]
    
    if total_weight > 0:
        avg_score = total_score / total_weight
        attrition_score = min(100, max(0, (avg_score - 1) * 25))
        return round(attrition_score, 1)
    
    return 50

def get_risk_level(score):
    """Get risk level based on score"""
    if score <= 30:
        return "Low", "success"
    elif score <= 70:
        return "Moderate", "warning"
    else:
        return "High", "danger"

def get_gemini_summary(employee_data, scores, attrition_score):
    """Get AI summary from Google Gemini"""
    try:
        client = genai.Client()
        
        prompt = f"""
        Please provide a professional HR summary for this employee:
        
        Name: {employee_data['Name']}
        Employee ID: {employee_data['EmployeeID']}
        Department: {employee_data['Department']}
        Age: {employee_data['Age']}
        Tenure: {employee_data['Tenure_Years']} years, {employee_data['Tenure_Months']} months
        Recent Promotion: {employee_data['Recent_Promotion']}
        Employment Type: {employee_data['Employment_Type']}
        Manager: {employee_data['Manager']}
        
        Psychometric Scores (1-5 scale):
        - Job Embeddedness: {scores.get('job_embeddedness', 'N/A')}
        - Perceived Organizational Support: {scores.get('perceived_organizational_support', 'N/A')}
        - Burnout: {scores.get('burnout_olbi', 'N/A')}
        - Job Satisfaction: {scores.get('job_satisfaction_moaq', 'N/A')}
        - Psychological Safety: {scores.get('psychological_safety', 'N/A')}
        - Work Engagement: {scores.get('work_engagement', 'N/A')}
        
        Attrition Risk Score: {attrition_score}/100
        
        Please provide a concise 3-4 sentence summary focusing on:
        1. Key risk factors
        2. Positive indicators
        3. Specific actionable recommendations for HR
        4. Suggested follow-up actions
        
        Make it professional and actionable for HR professionals.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text
        
    except Exception as e:
        return f"Unable to generate AI summary: {str(e)}"

def create_download_report(employee_data, scores, attrition_score, ai_summary):
    """Create downloadable employee report"""
    risk_level, _ = get_risk_level(attrition_score)
    
    report = f"""
# Employee Attrition Risk Report

## Employee Information
- **Name:** {employee_data['Name']}
- **Employee ID:** {employee_data['EmployeeID']}
- **Department:** {employee_data['Department']}
- **Age:** {employee_data['Age']}
- **Tenure:** {employee_data['Tenure_Years']} years, {employee_data['Tenure_Months']} months
- **Recent Promotion:** {employee_data['Recent_Promotion']}
- **Employment Type:** {employee_data['Employment_Type']}
- **Manager:** {employee_data['Manager']}

## Attrition Risk Assessment
- **Overall Risk Score:** {attrition_score}/100
- **Risk Level:** {risk_level}

## Psychometric Scores (1-5 scale)
"""
    
    for model_key, score in scores.items():
        model_name = MODEL_DEFS[model_key]['name']
        report += f"- **{model_name}:** {score}\n"
    
    report += f"""
## AI-Generated Summary
{ai_summary}

## Recommendations
"""
    
    # Generate recommendations based on scores
    for model_key, score in scores.items():
        if score > 3.5:
            if model_key == 'burnout_olbi':
                report += "- **High burnout detected:** Consider wellness programs, workload reduction, and stress management initiatives.\n"
            elif model_key == 'job_satisfaction_moaq':
                report += "- **Low job satisfaction:** Review compensation, work environment, and career development opportunities.\n"
            elif model_key == 'job_embeddedness':
                report += "- **Low job embeddedness:** Build stronger organizational and community ties.\n"
            elif model_key == 'perceived_organizational_support':
                report += "- **Low perceived organizational support:** Improve communication, recognition, and employee care programs.\n"
            elif model_key == 'psychological_safety':
                report += "- **Low psychological safety:** Implement team building, open communication, and leadership training.\n"
            elif model_key == 'work_engagement':
                report += "- **Low work engagement:** Focus on meaningful work, autonomy, and growth opportunities.\n"
    
    if not any(score > 3.5 for score in scores.values()):
        report += "- Overall risk is manageable. Continue monitoring and maintain positive practices.\n"
    
    report += f"""
---
*Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*
"""
    
    return report

def main():
    # Header
    st.markdown('<h1 class="main-header">Breakage</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Attrition Risk Detector - Professional HR Analytics Dashboard</p>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    if df is None:
        st.error("Failed to load employee data. Please ensure the CSV files are available.")
        return
    
    # Calculate scores
    psychometric_scores = calculate_psychometric_scores(df)
    
    # Add scores to dataframe
    df['Attrition_Score'] = df['EmployeeID'].apply(lambda x: calculate_attrition_score(psychometric_scores.get(x, {})))
    
    # Sidebar filters
    st.sidebar.markdown("## Filters")
    
    # Department filter
    departments = ['All'] + sorted(df['Department'].unique().tolist())
    selected_dept = st.sidebar.selectbox("Department", departments)
    
    # Risk level filter
    risk_levels = ['All', 'Low', 'Moderate', 'High']
    selected_risk = st.sidebar.selectbox("Risk Level", risk_levels)
    
    # Filter data
    filtered_df = df.copy()
    if selected_dept != 'All':
        filtered_df = filtered_df[filtered_df['Department'] == selected_dept]
    
    if selected_risk != 'All':
        filtered_df['Risk_Level'] = filtered_df['Attrition_Score'].apply(lambda x: get_risk_level(x)[0])
        filtered_df = filtered_df[filtered_df['Risk_Level'] == selected_risk]
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_employees = len(filtered_df)
        st.metric("Total Employees", total_employees)
    
    with col2:
        avg_risk = filtered_df['Attrition_Score'].mean()
        st.metric("Avg Risk Score", f"{avg_risk:.1f}")
    
    with col3:
        high_risk = len(filtered_df[filtered_df['Attrition_Score'] > 70])
        st.metric("High Risk", high_risk)
    
    with col4:
        low_risk = len(filtered_df[filtered_df['Attrition_Score'] <= 30])
        st.metric("Low Risk", low_risk)
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Department Distribution & Risk Analysis")
        
        # Create interactive pie chart
        dept_counts = filtered_df['Department'].value_counts()
        fig_pie = px.pie(
            values=dept_counts.values,
            names=dept_counts.index,
            title="Employee Distribution by Department",
            color_discrete_map=DEPARTMENT_COLORS
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### Risk Distribution")
        
        # Risk level distribution
        filtered_df['Risk_Level'] = filtered_df['Attrition_Score'].apply(lambda x: get_risk_level(x)[0])
        risk_counts = filtered_df['Risk_Level'].value_counts()
        
        fig_risk = px.bar(
            x=risk_counts.index,
            y=risk_counts.values,
            title="Risk Level Distribution",
            color=risk_counts.index,
            color_discrete_map={'Low': COLORS['success'], 'Moderate': COLORS['warning'], 'High': COLORS['danger']}
        )
        fig_risk.update_layout(showlegend=False)
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Department risk analysis
    st.markdown("### Department Risk Analysis")
    
    dept_risk = filtered_df.groupby('Department')['Attrition_Score'].agg(['mean', 'count']).reset_index()
    dept_risk.columns = ['Department', 'Average Risk', 'Employee Count']
    
    fig_dept_risk = px.bar(
        dept_risk,
        x='Department',
        y='Average Risk',
        title="Average Attrition Risk by Department",
        color='Department',
        color_discrete_map=DEPARTMENT_COLORS,
        text='Average Risk'
    )
    fig_dept_risk.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    st.plotly_chart(fig_dept_risk, use_container_width=True)
    
    # Employee details section
    st.markdown("### Employee Details")
    
    # Employee selector
    employee_options = [f"{row['Name']} ({row['EmployeeID']})" for _, row in filtered_df.iterrows()]
    selected_employee = st.selectbox("Select Employee", employee_options)
    
    if selected_employee:
        # Extract employee ID
        emp_id = selected_employee.split('(')[1].split(')')[0]
        employee_data = filtered_df[filtered_df['EmployeeID'] == int(emp_id)].iloc[0]
        scores = psychometric_scores.get(int(emp_id), {})
        attrition_score = employee_data['Attrition_Score']
        risk_level, risk_color = get_risk_level(attrition_score)
        
        # Employee information cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="department-card">
                <h4>Employee Information</h4>
                <p><strong>Name:</strong> {employee_data['Name']}</p>
                <p><strong>ID:</strong> {employee_data['EmployeeID']}</p>
                <p><strong>Department:</strong> {employee_data['Department']}</p>
                <p><strong>Manager:</strong> {employee_data['Manager']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="department-card">
                <h4>Employment Details</h4>
                <p><strong>Age:</strong> {employee_data['Age']}</p>
                <p><strong>Tenure:</strong> {employee_data['Tenure_Years']}y {employee_data['Tenure_Months']}m</p>
                <p><strong>Type:</strong> {employee_data['Employment_Type']}</p>
                <p><strong>Promotion:</strong> {employee_data['Recent_Promotion']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card risk-{risk_color}">
                <h3>Attrition Risk</h3>
                <h2>{attrition_score:.1f}%</h2>
                <p>{risk_level} Risk</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Psychometric scores visualization
        st.markdown("### Psychometric Assessment")
        
        if scores:
            # Create radar chart for psychometric scores
            fig_radar = go.Figure()
            
            categories = [MODEL_DEFS[key]['name'] for key in scores.keys()]
            values = list(scores.values())
            
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Employee Scores',
                line_color=COLORS['primary']
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )),
                showlegend=False,
                title="Psychometric Profile"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
        
        # AI Summary section
        st.markdown("### AI-Powered HR Summary")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("Generate AI Summary", key="generate_summary"):
                with st.spinner("Generating AI summary..."):
                    ai_summary = get_gemini_summary(employee_data, scores, attrition_score)
                    st.session_state.ai_summary = ai_summary
                    st.session_state.employee_data = employee_data
                    st.session_state.scores = scores
                    st.session_state.attrition_score = attrition_score
        
        with col2:
            if 'ai_summary' in st.session_state:
                # Create download button
                report_content = create_download_report(
                    st.session_state.employee_data,
                    st.session_state.scores,
                    st.session_state.attrition_score,
                    st.session_state.ai_summary
                )
                
                st.download_button(
                    label="📥 Download Report",
                    data=report_content,
                    file_name=f"employee_report_{employee_data['Name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    help="Download comprehensive employee report"
                )
        
        # Display AI summary
        if 'ai_summary' in st.session_state:
            st.markdown("#### AI Analysis")
            st.info(st.session_state.ai_summary)
        
        # Detailed scores table
        if scores:
            st.markdown("### Detailed Scores")
            
            score_data = []
            for model_key, score in scores.items():
                model_info = MODEL_DEFS[model_key]
                score_data.append({
                    'Assessment': model_info['name'],
                    'Score': score,
                    'Author': model_info['author'],
                    'Description': model_info['description']
                })
            
            score_df = pd.DataFrame(score_data)
            st.dataframe(score_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #6b7280;'>Breakage - Professional Attrition Risk Detection System</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 