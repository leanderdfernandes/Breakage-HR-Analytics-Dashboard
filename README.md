# Breakage - Professional Attrition Risk Detector

A modern, professional HR analytics dashboard built with Streamlit that provides comprehensive attrition risk analysis and AI-powered insights.
 ![image](https://github.com/user-attachments/assets/e17703ee-baad-47c1-a85e-43bca3617f80)


## Features

### 🎯 Core Functionality
- **Interactive Dashboard**: Professional UI with real-time data visualization
- **Department Filtering**: Click on pie chart sections to filter by department
- **Risk Assessment**: Comprehensive psychometric scoring system
- **AI-Powered Insights**: Google Gemini integration for intelligent HR summaries
- **Downloadable Reports**: Professional employee reports with actionable insights

### 📊 Visual Analytics
- **Interactive Pie Charts**: Department distribution with click-to-filter functionality
- **Risk Distribution Bars**: Visual representation of risk levels
- **Department Risk Analysis**: Comparative risk assessment across departments
- **Psychometric Radar Charts**: Individual employee assessment profiles
- **Professional Color Coding**: Consistent, modern color scheme

### 🤖 AI Integration
- **Smart Summaries**: AI-generated HR insights and recommendations
- **Actionable Recommendations**: Specific, data-driven suggestions
- **Professional Reports**: Downloadable employee assessments

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Breakage
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Gemini API**
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Update the `GEMINI_API_KEY` in `streamlit_app.py`

4. **Prepare your data**
   - Place your employee CSV file in the project directory
   - Supported files: `employee_data.csv` or `employee_data_enhanced.csv`

## Usage

### Starting the Application
```bash
streamlit run streamlit_app.py
```

The application will open in your default browser at `http://localhost:8501`

### Key Features

#### 1. Interactive Department Filtering
- Click on any section of the department pie chart to filter data
- Click anywhere else to return to full dataset view
- Use sidebar filters for additional customization

#### 2. Employee Analysis
- Select any employee from the dropdown
- View comprehensive psychometric scores
- Generate AI-powered HR summaries
- Download professional reports

#### 3. Risk Assessment
- Real-time risk calculation based on multiple psychometric factors
- Color-coded risk levels (Low/Moderate/High)
- Department-level risk analysis

#### 4. AI Summary Generation
- Click "Generate AI Summary" for intelligent insights
- AI provides actionable recommendations
- Professional language suitable for HR professionals

#### 5. Report Download
- Download comprehensive employee reports
- Includes all scores, risk assessment, and AI summary
- Professional formatting for HR documentation

## Data Structure

The application expects CSV data with the following columns:

### Required Columns
- `Name`: Employee name
- `EmployeeID`: Unique employee identifier
- `Department`: Employee department
- `Age`: Employee age
- `Tenure_Years`: Years of service
- `Tenure_Months`: Months of service
- `Recent_Promotion`: "Yes" or "No"
- `Employment_Type`: "Full Time" or "Part Time"
- `Manager`: Manager name

### Psychometric Columns
The application automatically calculates scores from these columns:

#### Job Embeddedness (Crossley et al., 2007)
- `Job_Embeddedness1` through `Job_Embeddedness7`

#### Perceived Organizational Support (Eisenberger et al., 1986)
- `POS1` through `POS10`

#### Burnout OLBI (Demerouti et al., 2001)
- `Burnout_Exhaustion1` through `Burnout_Exhaustion4`
- `Burnout_Disengagement1` through `Burnout_Disengagement4`

#### Job Satisfaction MOAQ (Cammann et al., 1983)
- `Job_Satisfaction1` through `Job_Satisfaction3`

#### Psychological Safety (Edmondson, 1999)
- `Psych_Safety1` through `Psych_Safety7`

#### Work Engagement UWES-9 (Schaufeli et al., 2006)
- `UWES_Vigor1` through `UWES_Vigor3`
- `UWES_Dedication1` through `UWES_Dedication3`
- `UWES_Absorption1` through `UWES_Absorption3`

## Psychometric Models

The application uses validated psychometric instruments:

### Job Embeddedness
- **Purpose**: Measures how embedded an employee is in their job and organization
- **Scale**: 1-5 (higher = more embedded)
- **Impact**: Lower scores indicate higher attrition risk

### Perceived Organizational Support
- **Purpose**: Employee perception of organizational support and care
- **Scale**: 1-5 (higher = more support)
- **Impact**: Lower scores indicate higher attrition risk

### Burnout (OLBI)
- **Purpose**: Measures emotional exhaustion and disengagement
- **Scale**: 1-5 (higher = more burnout)
- **Impact**: Higher scores indicate higher attrition risk

### Job Satisfaction (MOAQ)
- **Purpose**: Overall job satisfaction and contentment
- **Scale**: 1-5 (higher = more satisfied)
- **Impact**: Lower scores indicate higher attrition risk

### Psychological Safety
- **Purpose**: Perceived safety for interpersonal risk-taking
- **Scale**: 1-5 (higher = more safety)
- **Impact**: Lower scores indicate higher attrition risk

### Work Engagement (UWES-9)
- **Purpose**: Vigor, dedication, and absorption in work
- **Scale**: 1-5 (higher = more engaged)
- **Impact**: Lower scores indicate higher attrition risk

## Risk Calculation

The overall attrition risk score (0-100) is calculated using weighted averages:

- **Job Embeddedness**: 25% weight
- **Perceived Organizational Support**: 20% weight
- **Burnout**: 25% weight
- **Job Satisfaction**: 20% weight
- **Psychological Safety**: 5% weight
- **Work Engagement**: 5% weight

### Risk Levels
- **Low Risk**: 0-30% (Green)
- **Moderate Risk**: 31-70% (Yellow)
- **High Risk**: 71-100% (Red)

## Customization

### Adding New Departments
The application automatically detects departments from your CSV data and assigns professional colors.

### Modifying Risk Weights
Edit the weights in the `calculate_attrition_score()` function to adjust the importance of different factors.

### Customizing Colors
Update the `DEPARTMENT_COLORS` and `COLORS` dictionaries to match your organization's branding.

## Technical Details

### Architecture
- **Frontend**: Streamlit (Python web framework)
- **Visualization**: Plotly (interactive charts)
- **AI**: Google Gemini API
- **Data Processing**: Pandas & NumPy

### Performance
- Cached data loading for optimal performance
- Efficient filtering and calculations
- Responsive design for various screen sizes

### Security
- API keys stored as environment variables
- No sensitive data stored in session state
- Secure data handling practices

## Troubleshooting

### Common Issues

1. **CSV Loading Error**
   - Ensure your CSV file is in the correct directory
   - Check that column names match the expected format
   - Verify file encoding (UTF-8 recommended)

2. **API Key Issues**
   - Verify your Google Gemini API key is correct
   - Ensure you have sufficient API quota
   - Check internet connectivity

3. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Update to latest versions if needed

4. **Display Issues**
   - Clear browser cache
   - Try different browser
   - Check screen resolution compatibility

## Support

For technical support or feature requests, please contact the development team.

## License

This project is proprietary software. All rights reserved.

---

**Breakage** - Professional Attrition Risk Detection System 
