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
import requests
from PIL import Image
import io

# Set Streamlit theme to white background
st.set_page_config(
    page_title="Breakage - Attrition Risk Detector",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for white background and clean look
st.markdown("""
<style>
body, .stApp, .main, .block-container {
    background: #fff !important;
}
[data-testid="stHeader"], [data-testid="stSidebar"] {
    background: #fff !important;
}
.stRadio [role="radiogroup"] > label {
    background: #b2f7ef !important;
    color: #222831 !important;
    font-weight: 700;
    font-size: 1.1rem;
    border-radius: 8px;
    margin-right: 8px;
    padding: 0.7rem 2.2rem 0.7rem 2.2rem;
    cursor: pointer;
}
.stRadio [aria-checked="true"] {
    background: #00adb5 !important;
    color: #fff !important;
}
.stButton > button {
    background: #00adb5 !important;
    color: #fff !important;
    border-radius: 6px;
    font-weight: 600;
    border: none;
    padding: 0.5rem 1.2rem;
}
.stButton > button:hover {
    background: #00939c !important;
}
.stDataFrame, .stTable {
    background: #fff !important;
}
.header-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
    'primary': '#00adb5',
    'secondary': '#b2f7ef',
    'success': '#27ae60',
    'warning': '#f7d774',
    'danger': '#ff6b81',
    'info': '#393e46',
    'light': '#f8fafc',
    'dark': '#222831'
}

DEPARTMENT_COLORS = {
    'Sales': '#00adb5',
    'Marketing': '#9b59b6',
    'Engineering': '#2ecc71',
    'HR': '#f1c40f',
    'Finance': '#e67e22',
    'Operations': '#e74c3c',
    'IT': '#34495e',
    'Legal': '#fd79a8',
    'Customer Service': '#ec4899',
    'Research': '#6366f1'
}

def load_header_image():
    """Load header image from URL"""
    try:
        # Use a more reliable image URL
        url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&h=300&fit=crop"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return image
        else:
            return None
    except Exception as e:
        st.warning(f"Could not load header image: {str(e)}")
        return None

def create_psychometric_radar_chart(scores, employee_name):
    """Create a radar/spider chart for psychometric scores"""
    if not scores:
        return None
    
    # Prepare data for radar chart
    categories = []
    values = []
    
    for model_key, score in scores.items():
        if score != 'N/A' and isinstance(score, (int, float)):
            model_name = MODEL_DEFS[model_key]['name']
            categories.append(model_name)
            values.append(float(score))
    
    if not categories or len(categories) < 3:
        return None
    
    # Create radar chart
    fig = go.Figure()
    
    # Add the main radar trace
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 173, 181, 0.3)',
        line_color=COLORS['primary'],
        line_width=2,
        name='Employee Scores',
        hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}<br>Scale: 1-5<extra></extra>'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                ticktext=['1', '2', '3', '4', '5'],
                tickvals=[1, 2, 3, 4, 5],
                tickfont=dict(size=12),
                gridcolor='rgba(0,0,0,0.2)',
                linecolor='rgba(0,0,0,0.2)',
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=COLORS['dark']),
                gridcolor='rgba(0,0,0,0.1)',
                linecolor='rgba(0,0,0,0.1)',
            ),
            bgcolor='rgba(255,255,255,0.9)',
        ),
        showlegend=False,
        title=dict(
            text=f"Psychometric Profile: {employee_name}",
            x=0.5,
            font=dict(size=16, color=COLORS['dark'])
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_psychometric_bar_chart(scores, employee_name):
    """Create a horizontal bar chart for psychometric scores"""
    if not scores:
        return None
    
    # Prepare data
    categories = []
    values = []
    colors = []
    
    for model_key, score in scores.items():
        if score != 'N/A' and isinstance(score, (int, float)):
            model_name = MODEL_DEFS[model_key]['name']
            categories.append(model_name)
            values.append(float(score))
            
            # Color coding based on score
            if score <= 2:
                colors.append(COLORS['success'])
            elif score <= 3.5:
                colors.append(COLORS['warning'])
            else:
                colors.append(COLORS['danger'])
    
    if not categories:
        return None
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='white', width=1)
        ),
        text=[f'{v:.1f}' for v in values],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Score: %{x}<br>Scale: 1-5<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f"Psychometric Scores: {employee_name}",
            x=0.5,
            font=dict(size=16, color=COLORS['dark'])
        ),
        xaxis=dict(
            title="Score (1-5 scale)",
            range=[0, 5],
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=False
        ),
        yaxis=dict(
            title=None,
            gridcolor='rgba(0,0,0,0.1)',
            zeroline=False
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False
    )
    
    return fig

@st.cache_data
def load_data():
    """Load and process employee data"""
    try:
        # Try enhanced CSV first, fall back to original
        try:
            df = pd.read_csv("employee_data_enhanced.csv", dtype=str)
        except FileNotFoundError:
            df = pd.read_csv("employee_data.csv", dtype=str)
            # Add missing columns with realistic values
            df['Age'] = np.random.randint(22, 65, len(df)).astype(str)
            df['Tenure_Years'] = np.random.randint(0, 15, len(df)).astype(str)
            df['Tenure_Months'] = np.random.randint(0, 12, len(df)).astype(str)
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
                values = [float(row[col]) for col in columns if col in row and pd.notna(row[col])]
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
        return "Low", "#27ae60"
    elif score <= 70:
        return "Moderate", "#f7d774"
    else:
        return "High", "#ff6b81"

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

def create_interactive_pie_chart(df, selected_dept=None):
    """Create interactive pie chart with click-to-filter functionality"""
    dept_counts = df['Department'].value_counts()
    
    fig = px.pie(
        values=dept_counts.values,
        names=dept_counts.index,
        title="Employee Distribution by Department",
        color_discrete_map=DEPARTMENT_COLORS,
        hole=0.4  # Make it a donut chart
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Employees: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=16,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    return fig

def main():
    # Load and display header image with overlaid title (full width, no overlay, strong text shadow)
    header_image = load_header_image()
    if header_image:
        import base64
        from io import BytesIO
        buffered = BytesIO()
        header_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        st.markdown("""
        <div style="position: relative; width: 100vw; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;">
            <img src="data:image/jpeg;base64,{}" style="width: 100vw; max-width: 100%; height: 260px; object-fit: cover; display: block; margin: 0; padding: 0; border-radius: 0;" />
            <div style="position: absolute; top: 0; left: 0; width: 100vw; height: 260px; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none;">
                <h1 style="font-size: 4rem; font-weight: 900; color: #fff; text-align: center; margin: 0; text-shadow: 0 4px 24px #222, 0 2px 8px #222, 0 0 2px #222; letter-spacing: 2px;">Breakage</h1>
                <p style="font-size: 1.5rem; font-weight: 600; color: #fff; text-align: center; margin: 0.5rem 0 0 0; text-shadow: 0 2px 8px #222, 0 0 2px #222; letter-spacing: 1px;">Attrition Risk Detector - Professional HR Analytics Dashboard</p>
            </div>
        </div>
        <div style='height: 30px;'></div>
        """.format(img_str), unsafe_allow_html=True)
    else:
        # Fallback header with gradient background and title
        st.markdown("""
        <div style="width: 100vw; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw; height: 260px; background: linear-gradient(135deg, #00adb5 0%, #393e46 100%); border-radius: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <h1 style="font-size: 4rem; font-weight: 900; color: #fff; text-align: center; margin: 0; text-shadow: 0 4px 24px #222, 0 2px 8px #222, 0 0 2px #222; letter-spacing: 2px;">Breakage</h1>
            <p style="font-size: 1.5rem; font-weight: 600; color: #fff; text-align: center; margin: 0.5rem 0 0 0; text-shadow: 0 2px 8px #222, 0 0 2px #222; letter-spacing: 1px;">Attrition Risk Detector - Professional HR Analytics Dashboard</p>
        </div>
        <div style='height: 30px;'></div>
        """, unsafe_allow_html=True)
    df = load_data()
    if df is None:
        st.error("Failed to load employee data. Please ensure the CSV files are available.")
        return
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    for col in df.columns:
        if not isinstance(df[col], pd.Series):
            df[col] = pd.Series(df[col])
    psychometric_scores = calculate_psychometric_scores(df)
    df['Attrition_Score'] = df['EmployeeID'].astype(str).apply(lambda x: calculate_attrition_score(psychometric_scores.get(x, {})))

    # --- TOP TABS NAVIGATION ---
    tab1, tab2 = st.tabs(["Employee Data", "Create Report"])

    with tab1:
        st.markdown("## Company Dashboard")
        # Employee Table FIRST
        st.markdown("### Employee Table")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Total Employees", len(df))
        with col2:
            st.metric("📊 Avg Risk Score", f"{df['Attrition_Score'].mean():.1f}")
        with col3:
            st.metric("⚠️ High Risk", len(df[df['Attrition_Score'] > 70]))
        with col4:
            st.metric("✅ Low Risk", len(df[df['Attrition_Score'] <= 30]))
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### Attrition by Department")
            dept_counts = df['Department'].astype(str).value_counts()
            fig_pie = px.pie(
                values=dept_counts.values,
                names=dept_counts.index,
                color=dept_counts.index,
                color_discrete_map=DEPARTMENT_COLORS,
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#fff', width=2)))
            fig_pie.update_layout(paper_bgcolor='#fff', plot_bgcolor='#fff', showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            st.markdown("### Risk Distribution")
            df['Risk_Level'] = df['Attrition_Score'].apply(lambda x: get_risk_level(x)[0])
            risk_counts = df['Risk_Level'].value_counts()
            fig_risk = px.bar(
                x=risk_counts.index,
                y=risk_counts.values,
                title="Risk Level Distribution",
                color=risk_counts.index,
                color_discrete_map={'Low': '#27ae60', 'Moderate': '#f7d774', 'High': '#ff6b81'}
            )
            fig_risk.update_layout(showlegend=False, title_x=0.5, paper_bgcolor='#fff', plot_bgcolor='#fff', xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_risk, use_container_width=True)
        st.markdown("### Departmental Attrition Risk")
        dept_risk = df.groupby('Department', as_index=False)['Attrition_Score'].mean()
        fig_bar = px.bar(
            dept_risk,
            x='Department',
            y='Attrition_Score',
            color='Department',
            color_discrete_map=DEPARTMENT_COLORS,
            text='Attrition_Score',
            labels={'Attrition_Score': 'Avg Risk'}
        )
        fig_bar.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
        fig_bar.update_layout(yaxis=dict(range=[0, 100]), paper_bgcolor='#fff', plot_bgcolor='#fff')
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #6b7280; font-size: 0.9rem;'>Breakage - Professional Attrition Risk Detection System | Company Dashboard</p>", unsafe_allow_html=True)

    with tab2:
        st.markdown("## Employee Report")
        employee_options = [f"{row['Name']} ({row['EmployeeID']})" for _, row in df.iterrows()]
        selected_employee = st.selectbox("Select Employee", employee_options)
        if selected_employee:
            emp_id = selected_employee.split('(')[1].split(')')[0].strip(')')
            employee_data = df[df['EmployeeID'] == emp_id].iloc[0]
            scores = calculate_psychometric_scores(df).get(emp_id, {})
            attrition_score = employee_data['Attrition_Score']
            risk_level, risk_color = get_risk_level(attrition_score)
            # Profile Card
            st.markdown(f"""
            <div style='background:#f8fafc;border-radius:12px;padding:2rem 2rem 1rem 2rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);'>
                <h3 style='color:#00adb5;margin-bottom:0.5rem;'>Profile</h3>
                <b>Name:</b> {employee_data['Name']}<br>
                <b>ID:</b> {employee_data['EmployeeID']}<br>
                <b>Department:</b> {employee_data['Department']}<br>
                <b>Manager:</b> {employee_data['Manager']}<br>
                <b>Age:</b> {employee_data['Age']}<br>
                <b>Tenure:</b> {employee_data['Tenure_Years']}y {employee_data['Tenure_Months']}m<br>
                <b>Promotion:</b> {employee_data['Recent_Promotion']}<br>
                <b>Type:</b> {employee_data['Employment_Type']}<br>
            </div>
            """, unsafe_allow_html=True)
            # Professional Psychometric Scores Visualization
            st.markdown("#### Psychometric Scores")
            
            # Create tabs for different chart types
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Radar Chart", "Bar Chart", "Table"])
            
            with chart_tab1:
                radar_fig = create_psychometric_radar_chart(scores, employee_data['Name'])
                if radar_fig:
                    st.plotly_chart(radar_fig, use_container_width=True)
                else:
                    st.info("No psychometric data available for radar chart visualization.")
                    # Debug information
                    st.write("Debug - Available scores:", scores)
                    st.write("Debug - Score types:", {k: type(v).__name__ for k, v in scores.items()})
            
            with chart_tab2:
                bar_fig = create_psychometric_bar_chart(scores, employee_data['Name'])
                if bar_fig:
                    st.plotly_chart(bar_fig, use_container_width=True)
                else:
                    st.info("No psychometric data available for bar chart visualization.")
            
            with chart_tab3:
                score_data = []
                for model_key, model in MODEL_DEFS.items():
                    score = scores.get(model_key, 'N/A')
                    score_data.append({
                        'Assessment': model['name'],
                        'Score': score,
                        'Author': model['author']
                    })
                score_df = pd.DataFrame(score_data)
                st.dataframe(score_df, use_container_width=True, hide_index=True)
            # Risk Gradient
            st.markdown(f"<h3 style='color:#00adb5;'>Attrition Risk</h3>", unsafe_allow_html=True)
            pct = int(attrition_score)
            st.markdown(f"<span style='font-size:1.5rem;color:{risk_color};font-weight:700;'>{pct}%  ({risk_level})</span>", unsafe_allow_html=True)
            grad = f"linear-gradient(90deg, #a8e6cf {pct}%, #f7d774 {pct+10}%, #ff6b81 100%)"
            st.markdown(f"<div style='height:24px;width:100%;background:{grad};border-radius:8px;margin-bottom:12px;'></div>", unsafe_allow_html=True)
            # HR Recommendations
            st.markdown("#### HR Recommendations")
            recs = []
            for m, v in scores.items():
                if v != 'N/A' and v > 3.5:
                    if m == 'burnout_olbi':
                        recs.append("High burnout detected: Consider wellness programs, workload reduction, and stress management.")
                    elif m == 'job_satisfaction_moaq':
                        recs.append("Low job satisfaction: Review compensation, work environment, and career development.")
                    elif m == 'job_embeddedness':
                        recs.append("Low job embeddedness: Build stronger organizational/community ties.")
                    elif m == 'perceived_organizational_support':
                        recs.append("Low perceived organizational support: Improve communication, recognition, and employee care.")
                    elif m == 'psychological_safety':
                        recs.append("Low psychological safety: Implement team building, open communication, and leadership training.")
                    elif m == 'work_engagement':
                        recs.append("Low work engagement: Focus on meaningful work, autonomy, and growth opportunities.")
            if not recs:
                recs.append("Overall risk is manageable. Continue monitoring and maintain positive practices.")
            for rec in recs:
                st.markdown(f"- {rec}")
            # AI Summary
            if st.button("Generate AI Summary", key="generate_summary"):
                with st.spinner("🤖 Generating AI summary..."):
                    ai_summary = get_gemini_summary(employee_data, scores, attrition_score)
                    st.session_state.ai_summary = ai_summary
                    st.session_state.employee_data = employee_data
                    st.session_state.scores = scores
                    st.session_state.attrition_score = attrition_score
                    st.rerun()
            if 'ai_summary' in st.session_state and st.session_state.ai_summary:
                st.markdown("#### AI Analysis")
                st.info(st.session_state.ai_summary)
                report_content = create_download_report(
                    st.session_state.employee_data,
                    st.session_state.scores,
                    st.session_state.attrition_score,
                    st.session_state.ai_summary
                )
                st.download_button(
                    label="Download Employee Report",
                    data=report_content,
                    file_name=f"employee_report_{employee_data['Name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #6b7280; font-size: 0.9rem;'>Breakage - Professional Attrition Risk Detection System | Employee Report</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 