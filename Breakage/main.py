import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import pandas as pd
import requests
import json
import threading
from google import genai
import os


print("Prototype is running")


# Color palette for departments
DEPT_COLORS = [
    '#3498db', '#e67e22', '#2ecc71', '#9b59b6', '#e74c3c', '#f1c40f', '#1abc9c', '#34495e', '#7f8c8d', '#fd79a8'
]


# Google Gemini API configuration
GEMINI_API_KEY = "AIzaSyCnpRCQlbUnmEmPC77_P-gYXX2qG8eiTg4"
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY


MODEL_DEFS = {
    'job_embeddedness': {
        'name': 'Job Embeddedness',
        'author': 'Crossley et al., 2007',
        'upgrade': 'job_embeddedness_holtom',
        'upgrade_name': 'Job Embeddedness (Holtom et al., 2006)',
        'upgrade_author': 'Holtom et al., 2006',
        'csv_columns': ['Job_Embeddedness1', 'Job_Embeddedness2', 'Job_Embeddedness3', 'Job_Embeddedness4', 'Job_Embeddedness5', 'Job_Embeddedness6', 'Job_Embeddedness7']
    },
    'job_embeddedness_holtom': {
        'name': 'Job Embeddedness (21-item)',
        'author': 'Holtom et al., 2006',
        'downgrade': 'job_embeddedness',
        'downgrade_name': 'Job Embeddedness (Crossley et al., 2007)',
        'downgrade_author': 'Crossley et al., 2007',
        'csv_columns': ['Job_Embeddedness1', 'Job_Embeddedness2', 'Job_Embeddedness3', 'Job_Embeddedness4', 'Job_Embeddedness5', 'Job_Embeddedness6', 'Job_Embeddedness7']
    },
    'perceived_organizational_support': {
        'name': 'Perceived Organizational Support',
        'author': 'Eisenberger et al., 1986',
        'csv_columns': ['POS1', 'POS2', 'POS3', 'POS4', 'POS5', 'POS6', 'POS7', 'POS8', 'POS9', 'POS10']
    },
    'burnout_olbi': {
        'name': 'Burnout (OLBI)',
        'author': 'Demerouti et al., 2001',
        'upgrade': 'burnout_copenhagen',
        'upgrade_name': 'Burnout (CBI)',
        'upgrade_author': 'Kristensen et al., 2005',
        'csv_columns': ['Burnout_Exhaustion1', 'Burnout_Exhaustion2', 'Burnout_Exhaustion3', 'Burnout_Exhaustion4', 'Burnout_Disengagement1', 'Burnout_Disengagement2', 'Burnout_Disengagement3', 'Burnout_Disengagement4']
    },
    'burnout_copenhagen': {
        'name': 'Burnout (CBI)',
        'author': 'Kristensen et al., 2005',
        'downgrade': 'burnout_olbi',
        'downgrade_name': 'Burnout (OLBI)',
        'downgrade_author': 'Demerouti et al., 2001',
        'csv_columns': ['Burnout_Exhaustion1', 'Burnout_Exhaustion2', 'Burnout_Exhaustion3', 'Burnout_Exhaustion4', 'Burnout_Disengagement1', 'Burnout_Disengagement2', 'Burnout_Disengagement3', 'Burnout_Disengagement4']
    },
    'job_satisfaction_moaq': {
        'name': 'Job Satisfaction (MOAQ)',
        'author': 'Cammann et al., 1983',
        'upgrade': 'job_satisfaction_msq',
        'upgrade_name': 'Job Satisfaction (MSQ)',
        'upgrade_author': 'Weiss et al., 1967',
        'csv_columns': ['Job_Satisfaction1', 'Job_Satisfaction2', 'Job_Satisfaction3']
    },
    'job_satisfaction_msq': {
        'name': 'Job Satisfaction (MSQ)',
        'author': 'Weiss et al., 1967',
        'downgrade': 'job_satisfaction_moaq',
        'downgrade_name': 'Job Satisfaction (MOAQ)',
        'downgrade_author': 'Cammann et al., 1983',
        'csv_columns': ['Job_Satisfaction1', 'Job_Satisfaction2', 'Job_Satisfaction3']
    },
    'psychological_safety': {
        'name': 'Psychological Safety',
        'author': 'Edmondson, 1999',
        'csv_columns': ['Psych_Safety1', 'Psych_Safety2', 'Psych_Safety3', 'Psych_Safety4', 'Psych_Safety5', 'Psych_Safety6', 'Psych_Safety7']
    },
    'work_engagement': {
        'name': 'Work Engagement (UWES-9)',
        'author': 'Schaufeli et al., 2006',
        'csv_columns': ['UWES_Vigor1', 'UWES_Vigor2', 'UWES_Vigor3', 'UWES_Dedication1', 'UWES_Dedication2', 'UWES_Dedication3', 'UWES_Absorption1', 'UWES_Absorption2', 'UWES_Absorption3']
    },
}


DEFAULT_MODELS = [
    'job_embeddedness',
    'perceived_organizational_support',
    'burnout_olbi',
    'job_satisfaction_moaq',
]
OPTIONAL_MODELS = [
    'psychological_safety',
    'work_engagement',
]
MODEL_ORDER = [
    'job_embeddedness', 'job_embeddedness_holtom',
    'perceived_organizational_support',
    'burnout_olbi', 'burnout_copenhagen',
    'job_satisfaction_moaq', 'job_satisfaction_msq',
    'psychological_safety', 'work_engagement'
]


class AttritionApp:
    def __init__(self, root):
        print("AttritionApp.__init__ called")
        self.root = root
        self.root.title("Breakage - Attrition Risk Detector")
        self.root.geometry("1200x800")
        self.root.configure(bg='#e3f6fd')  # sky blue
        self.departments = []
        self.managers = []
        self.employees = []
        self.dept_color_map = {}
        self.next_color_idx = 0
        self.selected_employee_idx = None
        self.model_states = {k: (k in DEFAULT_MODELS) for k in MODEL_DEFS}
        for k in OPTIONAL_MODELS:
            self.model_states[k] = False
        self.employee_scores = defaultdict(dict)
        self.active_model_for_slider = {
            'job_embeddedness': 'job_embeddedness',
            'burnout_olbi': 'burnout_olbi',
            'job_satisfaction_moaq': 'job_satisfaction_moaq',
        }
        self.csv_data = None
        self.show_start_screen()


    def show_start_screen(self):
        print("show_start_screen called")
        self.clear_root()
        print("Root cleared")
        frame = tk.Frame(self.root, bg='#e3f6fd')
        frame.pack(fill='both', expand=True)
        print("Frame packed")
        tk.Label(frame, text="Breakage", font=("Segoe UI", 36, "bold"), fg="#00adb5", bg="#e3f6fd").pack(pady=100)
        print("Title label packed")
        tk.Label(frame, text="Attrition Risk Detector", font=("Segoe UI", 18), fg="#393e46", bg="#e3f6fd").pack(pady=10)
        print("Subtitle label packed")
        
        # Add Load CSV button
        tk.Button(frame, text="Load Employee Data from CSV", font=("Segoe UI", 14, "bold"), bg="#2ecc71", fg="#222831", width=25, height=2, command=self.load_csv_data, relief='flat', bd=0, activebackground="#27ae60").pack(pady=20)
        
        tk.Button(frame, text="Start", font=("Segoe UI", 16, "bold"), bg="#00adb5", fg="#222831", width=20, height=2, command=self.init_main_ui, relief='flat', bd=0, activebackground="#b2f7ef").pack(pady=20)
        print("Start button packed")


    def load_csv_data(self):
        """Load employee data from CSV and calculate psychometric scores"""
        try:
            # Try to load enhanced CSV first, fall back to original
            try:
                self.csv_data = pd.read_csv("employee_data_enhanced.csv")
            except FileNotFoundError:
                self.csv_data = pd.read_csv("employee_data.csv")
                # Add missing columns with default values
                self.csv_data['Age'] = np.random.randint(22, 65, len(self.csv_data))
                self.csv_data['Tenure_Years'] = np.random.randint(0, 15, len(self.csv_data))
                self.csv_data['Tenure_Months'] = np.random.randint(0, 12, len(self.csv_data))
                self.csv_data['Recent_Promotion'] = np.random.choice(["Yes", "No"], len(self.csv_data))
                self.csv_data['Employment_Type'] = np.random.choice(["Full Time", "Part Time"], len(self.csv_data))
                self.csv_data['Manager'] = "Manager " + np.random.randint(1, 10, len(self.csv_data)).astype(str)
            
            # Convert CSV data to employee format
            self.employees = []
            for _, row in self.csv_data.iterrows():
                emp = {
                    'Name': row['Name'],
                    'Employee ID': row['EmployeeID'],
                    'Age': str(row['Age']),
                    'Tenure Years': str(row['Tenure_Years']),
                    'Tenure Months': str(row['Tenure_Months']),
                    'Recent Promotion': row['Recent_Promotion'],
                    'Department': row['Department'],
                    'Manager': row['Manager'],
                    'Employment Type': row['Employment_Type'],
                    'Complaints': row.get('Complaints', ''),
                    'Improvements_Suggestions': row.get('Improvements_Suggestions', '')
                }
                self.employees.append(emp)
                
                # Calculate psychometric scores
                emp_id = row['EmployeeID']
                self.calculate_employee_scores(emp_id, row)
            
            # Update departments and managers lists
            self.departments = list(set([emp['Department'] for emp in self.employees if emp['Department']]))
            self.managers = list(set([emp['Manager'] for emp in self.employees if emp['Manager']]))
            
            # Assign colors to departments
            for dept in self.departments:
                if dept not in self.dept_color_map:
                    self.dept_color_map[dept] = DEPT_COLORS[self.next_color_idx % len(DEPT_COLORS)]
                    self.next_color_idx += 1
            
            messagebox.showinfo("Success", f"Loaded {len(self.employees)} employees from CSV with calculated psychometric scores!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV data: {str(e)}")


    def calculate_employee_scores(self, emp_id, row):
        """Calculate psychometric scores from CSV data"""
        scores = {}
        
        for model_key, model_def in MODEL_DEFS.items():
            if 'csv_columns' in model_def:
                columns = model_def['csv_columns']
                values = [row[col] for col in columns if col in row and pd.notna(row[col])]
                if values:
                    # Calculate average score (1-5 scale)
                    avg_score = np.mean(values)
                    scores[model_key] = avg_score
        
        self.employee_scores[emp_id] = scores


    def calculate_attrition_score(self, emp_id):
        """Calculate attrition risk score (0-100) from psychometric scores"""
        scores = self.employee_scores.get(emp_id, {})
        if not scores:
            return 50  # Neutral score if no data
        
        # Calculate weighted average based on model importance
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
                # Invert scores for positive constructs (higher = lower risk)
                if model in ['job_embeddedness', 'perceived_organizational_support', 'job_satisfaction_moaq', 'psychological_safety', 'work_engagement']:
                    adjusted_score = 6 - score  # Invert 1-5 scale
                else:
                    adjusted_score = score  # Keep burnout as is (higher = higher risk)
                
                total_score += adjusted_score * weights[model]
                total_weight += weights[model]
        
        if total_weight > 0:
            avg_score = total_score / total_weight
            # Convert to 0-100 scale
            attrition_score = min(100, max(0, (avg_score - 1) * 25))  # 1-5 scale to 0-100
            return attrition_score
        
        return 50


    def get_gemini_summary(self, emp_id):
        """Get employee summary from Google Gemini API"""
        emp = next((e for e in self.employees if e['Employee ID'] == emp_id), None)
        if not emp:
            return "Employee not found"
        
        scores = self.employee_scores.get(emp_id, {})
        attrition_score = self.calculate_attrition_score(emp_id)
        
        # Prepare data for Gemini API
        prompt = f"""
        Please provide a concise HR summary for this employee:
        
        Name: {emp['Name']}
        Department: {emp['Department']}
        Age: {emp['Age']}
        Tenure: {emp['Tenure Years']} years, {emp['Tenure Months']} months
        Recent Promotion: {emp['Recent Promotion']}
        Employment Type: {emp['Employment Type']}
        Manager: {emp['Manager']}
        
        Psychometric Scores (1-5 scale):
        - Job Embeddedness: {scores.get('job_embeddedness', 'N/A'):.2f}
        - Perceived Organizational Support: {scores.get('perceived_organizational_support', 'N/A'):.2f}
        - Burnout: {scores.get('burnout_olbi', 'N/A'):.2f}
        - Job Satisfaction: {scores.get('job_satisfaction_moaq', 'N/A'):.2f}
        - Psychological Safety: {scores.get('psychological_safety', 'N/A'):.2f}
        - Work Engagement: {scores.get('work_engagement', 'N/A'):.2f}
        
        Attrition Risk Score: {attrition_score:.1f}/100
        
        Complaints: {emp.get('Complaints', 'None')}
        Improvement Suggestions: {emp.get('Improvements_Suggestions', 'None')}
        
        Please provide a 2-3 sentence summary focusing on key risk factors and recommendations.
        """
        
        try:
            # Initialize Gemini client
            client = genai.Client()
            
            # Generate content using Gemini 2.5 Flash model
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            return response.text
                
        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"


    def clear_root(self):
        for w in self.root.winfo_children():
            w.destroy()


    def init_main_ui(self):
        self.clear_root()
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='#e3f6fd', borderwidth=0)
        style.configure('TNotebook.Tab', background='#b2f7ef', font=('Segoe UI', 12, 'bold'), padding=10)
        style.map('TNotebook.Tab', background=[('selected', '#00adb5')], foreground=[('selected', '#fff')])
        self.tab_control = ttk.Notebook(self.root, style='TNotebook')
        self.tab_emp = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_report = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_control.add(self.tab_emp, text='Employee Data')
        self.tab_control.add(self.tab_report, text='Create Report')
        self.tab_control.pack(expand=1, fill='both')
        self.init_employee_tab()
        self.init_report_tab()


    def init_employee_tab(self):
        frame = self.tab_emp
        for w in frame.winfo_children():
            w.destroy()
        
        # Add Load CSV button at the top
        load_frame = tk.Frame(frame, bg='#e3f6fd')
        load_frame.pack(fill='x', padx=10, pady=5)
        tk.Button(load_frame, text="Load CSV Data", command=self.load_csv_data, bg='#2ecc71', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        # Top: Add/Edit Employee
        add_frame = tk.LabelFrame(frame, text="Add/Edit Employee", padx=10, pady=10, bg='#e3f6fd', font=('Segoe UI', 12, 'bold'), fg='#222831')
        add_frame.pack(fill='x', padx=10, pady=5)
        self.emp_fields = {}
        # Name
        tk.Label(add_frame, text="Name:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=0, sticky='e', padx=(0,2))
        self.emp_fields['Name'] = tk.Entry(add_frame, width=20, font=('Segoe UI', 10))
        self.emp_fields['Name'].grid(row=0, column=1, padx=(0,18))
        # Employee ID
        tk.Label(add_frame, text="Employee ID:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=2, sticky='e', padx=(0,2))
        self.emp_fields['Employee ID'] = tk.Entry(add_frame, width=15, font=('Segoe UI', 10))
        self.emp_fields['Employee ID'].grid(row=0, column=3, padx=(0,18))
        # Age
        tk.Label(add_frame, text="Age:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=4, sticky='e', padx=(0,2))
        self.emp_fields['Age'] = tk.Entry(add_frame, width=5, font=('Segoe UI', 10))
        self.emp_fields['Age'].grid(row=0, column=5, padx=(0,18))
        # Tenure (Years/Months)
        tk.Label(add_frame, text="Tenure:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=6, sticky='e', padx=(0,2))
        self.emp_fields['Tenure Years'] = tk.Entry(add_frame, width=4, font=('Segoe UI', 10))
        self.emp_fields['Tenure Years'].grid(row=0, column=7, padx=(0,2))
        tk.Label(add_frame, text="yrs", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=8, sticky='w', padx=(0,2))
        self.emp_fields['Tenure Months'] = tk.Entry(add_frame, width=4, font=('Segoe UI', 10))
        self.emp_fields['Tenure Months'].grid(row=0, column=9, padx=(0,2))
        tk.Label(add_frame, text="mo", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=10, sticky='w', padx=(0,18))
        # Recent Promotion (Yes/No radio buttons)
        tk.Label(add_frame, text="Recent Promotion:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=11, sticky='e', padx=(0,2))
        self.promotion_var = tk.StringVar(value='No')
        tk.Radiobutton(add_frame, text="Yes", variable=self.promotion_var, value='Yes', bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=12, sticky='w', padx=(0,2))
        tk.Radiobutton(add_frame, text="No", variable=self.promotion_var, value='No', bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=0, column=13, sticky='w', padx=(0,18))
        # Department
        tk.Label(add_frame, text="Department:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=1, column=0, sticky='e', padx=(0,2))
        self.dept_var = tk.StringVar()
        self.dept_combo = ttk.Combobox(add_frame, textvariable=self.dept_var, values=self.departments, state='readonly', width=18, font=('Segoe UI', 10))
        self.dept_combo.grid(row=1, column=1, padx=(0,2))
        tk.Button(add_frame, text="+ Add", command=self.add_department, bg='#b2f7ef', font=('Segoe UI', 10, 'bold')).grid(row=1, column=2, padx=(0,18))
        # Manager
        tk.Label(add_frame, text="Manager:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=1, column=3, sticky='e', padx=(0,2))
        self.mgr_var = tk.StringVar()
        self.mgr_combo = ttk.Combobox(add_frame, textvariable=self.mgr_var, values=self.managers, state='readonly', width=18, font=('Segoe UI', 10))
        self.mgr_combo.grid(row=1, column=4, padx=(0,2))
        tk.Button(add_frame, text="+ Add", command=self.add_manager, bg='#b2f7ef', font=('Segoe UI', 10, 'bold')).grid(row=1, column=5, padx=(0,18))
        # Employment Type
        tk.Label(add_frame, text="Employment Type:", bg='#e3f6fd', font=('Segoe UI', 10)).grid(row=2, column=0, sticky='e', padx=(0,2))
        self.emp_fields['Employment Type'] = ttk.Combobox(add_frame, values=['Full Time', 'Part Time'], state='readonly', width=15, font=('Segoe UI', 10))
        self.emp_fields['Employment Type'].grid(row=2, column=1, padx=(0,18))
        # Buttons
        tk.Button(add_frame, text="Add/Update Employee", command=self.save_employee, bg='#00adb5', fg='white', font=('Segoe UI', 10, 'bold'), relief='flat').grid(row=2, column=3, padx=5)
        tk.Button(add_frame, text="Clear", command=self.clear_emp_form, bg='#b2f7ef', font=('Segoe UI', 10, 'bold')).grid(row=2, column=4, padx=5)
        tk.Button(add_frame, text="Delete Selected Employee", command=self.delete_employee, bg='#e74c3c', fg='white').grid(row=2, column=5, padx=5, sticky='w')
        # Table
        table_frame = tk.Frame(frame, bg='#e3f6fd')
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        columns = ("Status", "Name", "Employee ID", "Age", "Tenure", "Recent Promotion", "Department", "Manager", "Employment Type")
        self.emp_table = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse', height=8, style='Custom.Treeview')
        style = ttk.Style()
        style.configure('Custom.Treeview', font=('Segoe UI', 10), rowheight=28, background='#e3f6fd', fieldbackground='#e3f6fd')
        for col in columns:
            self.emp_table.heading(col, text=col)
            if col == "Status":
                self.emp_table.column(col, width=40, anchor='center')
            else:
                self.emp_table.column(col, width=120)
        self.emp_table.pack(side='left', fill='both', expand=True)
        self.emp_table.bind('<<TreeviewSelect>>', self.on_emp_select)
        self.emp_table.bind('<Button-1>', self.on_flag_single_left)
        self.emp_table.bind('<Double-Button-1>', self.on_flag_double_left)
        self.emp_table.bind('<Button-3>', self.on_flag_single_right)
        self.emp_table.bind('<Double-Button-3>', self.on_flag_double_right)
        # Store flag status by Employee ID
        self.flag_status = {}  # {emp_id: 'flag'|'hazard'|'tick'|''}
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.emp_table.yview)
        self.emp_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        # Mousewheel scroll
        self.emp_table.bind('<MouseWheel>', lambda e: self.emp_table.yview_scroll(int(-1*(e.delta/120)), 'units'))
        # Bar chart area
        self.bar_chart_frame = tk.Frame(frame, bg='#e3f6fd')
        self.bar_chart_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.update_emp_table()
        self.update_bar_charts()


    def add_department(self):
        dept = simpledialog.askstring("Add Department", "Enter new department name:")
        if dept and dept not in self.departments:
            self.departments.append(dept)
            self.dept_combo['values'] = self.departments
            if dept not in self.dept_color_map:
                self.dept_color_map[dept] = DEPT_COLORS[self.next_color_idx % len(DEPT_COLORS)]
                self.next_color_idx += 1


    def add_manager(self):
        mgr = simpledialog.askstring("Add Manager", "Enter new manager name:")
        if mgr and mgr not in self.managers:
            self.managers.append(mgr)
            self.mgr_combo['values'] = self.managers


    def save_employee(self):
        data = {k: v.get() if hasattr(v, 'get') else v.get() for k, v in self.emp_fields.items()}
        data['Department'] = self.dept_var.get()
        data['Manager'] = self.mgr_var.get()
        if not data['Name'] or not data['Employee ID']:
            messagebox.showerror("Error", "Name and Employee ID are required!")
            return
        idx = None
        for i, emp in enumerate(self.employees):
            if emp['Employee ID'] == data['Employee ID']:
                idx = i
                break
        if idx is not None:
            self.employees[idx] = data
        else:
            self.employees.append(data)
        self.update_emp_table()
        self.clear_emp_form()
        self.update_bar_charts()
        self.update_report_emp_dropdown()


    def clear_emp_form(self):
        for v in self.emp_fields.values():
            if hasattr(v, 'delete'):
                v.delete(0, tk.END)
            elif hasattr(v, 'set'):
                v.set('')
        self.dept_var.set('')
        self.mgr_var.set('')
        self.selected_employee_idx = None


    def update_emp_table(self):
        self.emp_table.delete(*self.emp_table.get_children())
        for emp in self.employees:
            tenure_years = emp.get('Tenure Years', '')
            tenure_months = emp.get('Tenure Months', '')
            try:
                y = int(tenure_years)
            except (ValueError, TypeError):
                y = 0
            try:
                m = int(tenure_months)
            except (ValueError, TypeError):
                m = 0
            tenure_str = ''
            if y == 1:
                tenure_str += '1 year'
            elif y > 1:
                tenure_str += f'{y} years'
            if m > 0:
                if tenure_str:
                    tenure_str += ' '
                tenure_str += f'{m} month' + ('s' if m > 1 else '')
            if not tenure_str:
                tenure_str = '0 months'
            emp_id = emp.get('Employee ID', '')
            status = self.flag_status.get(emp_id, '')
            if status == 'flag':
                icon = '🚩'
            elif status == 'hazard':
                icon = '⚠️'
            elif status == 'tick':
                icon = '✅'
            else:
                icon = ''
            row = (
                icon,
                emp.get('Name', ''),
                emp_id,
                emp.get('Age', ''),
                tenure_str,
                emp.get('Recent Promotion', ''),
                emp.get('Department', ''),
                emp.get('Manager', ''),
                emp.get('Employment Type', ''),
            )
            self.emp_table.insert('', 'end', values=row)


    def on_emp_select(self, event):
        sel = self.emp_table.selection()
        if not sel:
            return
        idx = self.emp_table.index(sel[0])
        emp = self.employees[idx]
        self.selected_employee_idx = idx
        for k, v in self.emp_fields.items():
            if hasattr(v, 'delete'):
                v.delete(0, tk.END)
                v.insert(0, emp.get(k, ''))
            elif hasattr(v, 'set'):
                v.set(emp.get(k, ''))
        self.dept_var.set(emp.get('Department', ''))
        self.mgr_var.set(emp.get('Manager', ''))


    def delete_employee(self):
        sel = self.emp_table.selection()
        if not sel:
            return
        idx = self.emp_table.index(sel[0])
        emp_id = self.employees[idx]['Employee ID']
        del self.employees[idx]
        if emp_id in self.employee_scores:
            del self.employee_scores[emp_id]
        self.update_emp_table()
        self.update_bar_charts()
        self.clear_emp_form()
        self.update_report_emp_dropdown()


    def update_bar_charts(self, highlight_dept=None):
        for w in self.bar_chart_frame.winfo_children():
            w.destroy()
        if not self.employees:
            return
        # Donut chart: department color-coded, interactive
        donut_fig, donut_ax = plt.subplots(figsize=(3,3))
        dept_counts = {d:0 for d in self.departments}
        for emp in self.employees:
            dept = emp['Department']
            if dept:
                dept_counts[dept] += 1
        depts = [d for d in self.departments if dept_counts[d]>0]
        sizes = [dept_counts[d] for d in depts]
        colors = [self.dept_color_map.get(d, '#7f8c8d') for d in depts]
        wedges, texts, *_ = donut_ax.pie(sizes, labels=depts, colors=colors, startangle=90, wedgeprops=dict(width=0.4), labeldistance=1.05)
        donut_ax.set_title('Overall Attrition Risk by Department')
        def on_donut_click(event):
            if event.inaxes == donut_ax:
                for i, w in enumerate(wedges):
                    if w.contains(event)[0]:
                        self.update_bar_charts(highlight_dept=depts[i])
                        return
        donut_fig.canvas.mpl_connect('button_press_event', on_donut_click)
        if highlight_dept:
            for i, d in enumerate(depts):
                wedges[i].set_alpha(1.0 if d==highlight_dept else 0.2)
        donut_canvas = FigureCanvasTkAgg(donut_fig, master=self.bar_chart_frame)
        donut_canvas.draw()
        donut_canvas.get_tk_widget().pack(side='left', padx=10)
        # Departmental bar chart
        from matplotlib.ticker import MaxNLocator
        dept_scores = defaultdict(list)
        for emp in self.employees:
            emp_id = emp['Employee ID']
            dept = emp['Department']
            score = self.get_emp_risk_score(emp_id)
            if dept:
                dept_scores[dept].append(score)
        depts = [d for d in self.departments if dept_scores[d]]
        avg_scores = [np.mean(dept_scores[d]) for d in depts]
        bar_colors = [self.dept_color_map.get(d, '#7f8c8d') for d in depts]
        bar_fig, bar_ax = plt.subplots(figsize=(5,3))
        bars = bar_ax.bar(depts, avg_scores, color=bar_colors, alpha=0.8, edgecolor='#222831', linewidth=1.5)
        bar_ax.set_ylabel('Avg Risk', fontname='Segoe UI', fontsize=10)
        bar_ax.set_title('Departmental Attrition Risk', fontname='Segoe UI', fontsize=12)
        bar_ax.set_ylim(1,5)
        bar_ax.set_xticklabels(depts, fontname='Segoe UI', fontsize=10)
        bar_ax.set_yticks([1,2,3,4,5])
        bar_ax.spines['top'].set_visible(False)
        bar_ax.spines['right'].set_visible(False)
        bar_ax.spines['left'].set_color('#b2f7ef')
        bar_ax.spines['bottom'].set_color('#b2f7ef')
        for i, bar in enumerate(bars):
            pct = int((avg_scores[i]-1)/4*100)
            bar_ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()-0.2, f"{pct}%", ha='center', va='top', color='white', fontweight='bold', fontname='Segoe UI', fontsize=10)
        def on_bar_click(event):
            if event.inaxes == bar_ax:
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        self.update_bar_charts(highlight_dept=depts[i])
                        return
        bar_fig.canvas.mpl_connect('button_press_event', on_bar_click)
        if highlight_dept:
            for i, d in enumerate(depts):
                bars[i].set_alpha(1.0 if d==highlight_dept else 0.2)
        bar_canvas = FigureCanvasTkAgg(bar_fig, master=self.bar_chart_frame)
        bar_canvas.draw()
        bar_canvas.get_tk_widget().pack(side='left', padx=10)
        # Employee search and scrollable bar chart
        emp_chart_frame = tk.Frame(self.bar_chart_frame, bg='#e3f6fd')
        emp_chart_frame.pack(side='left', fill='both', expand=True, padx=10)
        tk.Label(emp_chart_frame, text="Search Employee:", font=('Segoe UI', 10), bg='#e3f6fd').pack(anchor='nw')
        search_var = tk.StringVar()
        search_entry = tk.Entry(emp_chart_frame, textvariable=search_var, font=('Segoe UI', 10), width=20)
        search_entry.pack(anchor='nw', pady=2)
        canvas = tk.Canvas(emp_chart_frame, bg='#e3f6fd', highlightthickness=0, height=220)
        scroll_y = tk.Scrollbar(emp_chart_frame, orient='vertical', command=canvas.yview)
        frame_inner = tk.Frame(canvas, bg='#e3f6fd')
        canvas.create_window((0,0), window=frame_inner, anchor='nw')
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side='left', fill='both', expand=True)
        scroll_y.pack(side='right', fill='y')
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        canvas.bind_all('<MouseWheel>', on_mousewheel)
        def draw_emp_bars(*args):
            for w in frame_inner.winfo_children():
                w.destroy()
            filter_txt = search_var.get().lower()
            filtered = [e for e in self.employees if filter_txt in e['Name'].lower()]
            for i, emp in enumerate(filtered):
                emp_id = emp['Employee ID']
                risk = self.get_emp_risk_score(emp_id)
                color = self.dept_color_map.get(emp['Department'], '#7f8c8d')
                bar_frame = tk.Frame(frame_inner, bg='#e3f6fd', bd=1, relief='ridge')
                bar_frame.pack(fill='x', pady=2, padx=2)
                tk.Label(bar_frame, text=emp['Name'], width=18, anchor='w', font=('Segoe UI', 10, 'bold'), bg='#e3f6fd').pack(side='left')
                bar_canvas = tk.Canvas(bar_frame, width=180, height=18, bg='#e3f6fd', highlightthickness=0)
                bar_canvas.pack(side='left')
                pct = int((risk-1)/4*100)
                bar_canvas.create_rectangle(0, 2, pct*1.8, 16, fill=color, outline='')
                bar_canvas.create_text(90, 9, text=f"{pct}%", fill='white', font=('Segoe UI', 10, 'bold'))
                tk.Label(bar_frame, text=emp['Department'], width=12, anchor='w', font=('Segoe UI', 10), bg='#e3f6fd', fg=color).pack(side='left')
        search_var.trace_add('write', draw_emp_bars)
        draw_emp_bars()
        frame_inner.update_idletasks()
        canvas.config(scrollregion=canvas.bbox('all'))


    def get_emp_risk_score(self, emp_id):
        scores = self.employee_scores.get(emp_id, {})
        if not scores:
            return 1
        return np.mean(list(scores.values()))


    def get_emp_risk_level(self, emp_id):
        score = self.get_emp_risk_score(emp_id)
        if score <= 2.5:
            return 'Low'
        elif score <= 3.5:
            return 'Moderate'
        else:
            return 'High'


    def update_report_emp_dropdown(self):
        if hasattr(self, 'report_emp_combo'):
            vals = [f"{e['Name']} ({e['Employee ID']})" for e in self.employees]
            self.report_emp_combo['values'] = vals
            if vals:
                self.report_emp_combo.current(0)
                self.on_report_emp_select()


    def init_report_tab(self):
        frame = self.tab_report
        for w in frame.winfo_children():
            w.destroy()
        
        # Employee selector
        sel_frame = tk.Frame(frame)
        sel_frame.pack(pady=10)
        tk.Label(sel_frame, text="Choose Employee:").pack(side='left')
        self.report_emp_var = tk.StringVar()
        self.report_emp_combo = ttk.Combobox(sel_frame, textvariable=self.report_emp_var, values=[f"{e['Name']} ({e['Employee ID']})" for e in self.employees], state='readonly', width=30)
        self.report_emp_combo.pack(side='left', padx=5)
        self.report_emp_combo.bind('<<ComboboxSelected>>', self.on_report_emp_select)
        
        # Add Gemini Summary button
        tk.Button(sel_frame, text="Get AI Summary", command=self.show_gemini_summary, bg='#9b59b6', fg='white', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=5)
        
        # Sliders for models
        self.slider_frame = tk.LabelFrame(frame, text="Psychometric Scores")
        self.slider_frame.pack(fill='x', padx=10, pady=10)
        self.slider_vars = {}
        self.upgrade_buttons = {}
        self.model_check_vars = {}
        self.update_model_sliders()
        # Always-visible risk gradient area (now below psychometric scores)
        self.gradient_frame = tk.Frame(frame, bg='#e3f6fd')
        self.gradient_frame.pack(fill='x', padx=10, pady=(10, 0))
        self.update_risk_gradient()
        # Report output
        self.report_output_frame = tk.Frame(frame)
        self.report_output_frame.pack(fill='both', expand=True, padx=10, pady=10)
        # Live update on slider move
        self.slider_update_callback = self.live_update_report
        self.live_update_report()
        tk.Button(frame, text="Create Report", command=self.create_report, bg='#00adb5', fg='white', font=('Segoe UI', 10, 'bold'), relief='flat').pack(pady=10)
        tk.Button(frame, text="Save Employee Data", command=self.save_employee_data, bg='#00adb5', fg='white', font=('Segoe UI', 10, 'bold'), relief='flat').pack(pady=10)


    def update_risk_gradient(self):
        for w in self.gradient_frame.winfo_children():
            w.destroy()
        emp_name_id = getattr(self, 'report_emp_var', tk.StringVar()).get()
        emp = next((e for e in getattr(self, 'employees', []) if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            risk_score = 1
        else:
            emp_id = emp['Employee ID']
            checked_models = [m for m in self.slider_vars if self.model_states.get(m, False)]
            scores = [self.employee_scores[emp_id].get(m, 3) for m in checked_models]
            risk_score = np.mean(scores) if scores else 1
        if risk_score <= 2.5:
            risk_level = "Low"
            risk_color = "#27ae60"
            risk_pct = int((risk_score/2.5)*30)
        elif risk_score <= 3.5:
            risk_level = "Moderate"
            risk_color = "#f7d774"
            risk_pct = int(30+((risk_score-2.5)/1.0)*40)
        else:
            risk_level = "High"
            risk_color = "#ff6b81"
            risk_pct = int(70+((risk_score-3.5)/1.5)*30)
        header = tk.Label(self.gradient_frame, text="Attrition Risk", font=("Segoe UI", 16, "bold"), bg='#e3f6fd', fg="#393e46")
        header.pack(anchor='w', pady=(0,2))
        pct_label = tk.Label(self.gradient_frame, text=f"{risk_pct}%  ({risk_level})", font=("Segoe UI", 14, "bold"), bg='#e3f6fd', fg=risk_color)
        pct_label.pack(anchor='w', pady=(0,2))
        grad_fig, grad_ax = plt.subplots(figsize=(6,0.35), dpi=120)
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list('risk', ['#a8e6cf', '#f7d774', '#ff6b81'])
        grad = np.linspace(0,1,256).reshape(1,-1)
        grad_ax.imshow(grad, aspect='auto', cmap=cmap, extent=(0,100,0,1))
        # Bone white border for marker, slightly thinner
        grad_ax.axvline(risk_pct, color='#F9F6EE', lw=4, alpha=0.9, zorder=2)
        grad_ax.axvline(risk_pct, color=risk_color, lw=3, alpha=0.8, zorder=3)
        grad_ax.set_yticks([])
        grad_ax.set_xticks([])
        grad_ax.spines['top'].set_visible(False)
        grad_ax.spines['right'].set_visible(False)
        grad_ax.spines['left'].set_visible(False)
        grad_ax.spines['bottom'].set_visible(False)
        grad_fig.patch.set_alpha(0)
        grad_canvas = FigureCanvasTkAgg(grad_fig, master=self.gradient_frame)
        grad_canvas.draw()
        grad_canvas.get_tk_widget().pack(anchor='w', pady=(0,8))


    def update_model_sliders(self):
        for w in self.slider_frame.winfo_children():
            w.destroy()
        self.upgrade_buttons.clear()
        self.model_check_vars = {}
        row = 0
        tk.Button(self.slider_frame, text="Optional Models", command=self.show_optional_models_popup, font=("Segoe UI", 10)).grid(row=row, column=0, sticky='w', padx=5, pady=3)
        row += 1
        # Always show all main models and all optional models that are currently present in self.model_states (regardless of True/False)
        visible_models = [m for m in DEFAULT_MODELS] + [m for m in OPTIONAL_MODELS if m in self.model_states]
        shown = set()
        for m in MODEL_ORDER:
            if m not in visible_models or m in shown:
                continue
            # If this model is upgraded, only show the upgraded version in place
            if 'upgrade' in MODEL_DEFS.get(m, {}) and self.model_states.get(MODEL_DEFS[m]['upgrade'], False):
                upg = MODEL_DEFS[m]['upgrade']
                if upg not in shown and upg in visible_models:
                    m = upg
                    model = MODEL_DEFS[m]
                    shown.add(m)
                else:
                    continue
            # If this model is downgraded, only show the downgraded version in place
            elif 'downgrade' in MODEL_DEFS.get(m, {}) and self.model_states.get(MODEL_DEFS[m]['downgrade'], False):
                dng = MODEL_DEFS[m]['downgrade']
                if dng not in shown and dng in visible_models:
                    m = dng
                    model = MODEL_DEFS[m]
                    shown.add(m)
                else:
                    continue
            else:
                model = MODEL_DEFS[m]
                shown.add(m)
            check_var = tk.BooleanVar(value=self.model_states.get(m, False))
            self.model_check_vars[m] = check_var
            def on_check(m=m):
                self.model_states[m] = self.model_check_vars[m].get()
                self.slider_update_callback()
            check = tk.Checkbutton(self.slider_frame, variable=check_var, command=on_check)
            check.grid(row=row, column=0, sticky='w', padx=2)
            label = f"{model['name']} ({model['author']})"
            tk.Label(self.slider_frame, text=label).grid(row=row, column=1, sticky='w', padx=5, pady=3)
            if hasattr(self, 'just_upgraded') and self.just_upgraded == m:
                prev_val = 3
                self.just_upgraded = None
            else:
                prev_val = self.slider_vars[m].get() if m in self.slider_vars else 3
            var = tk.DoubleVar(value=prev_val)
            self.slider_vars[m] = var
            scale = tk.Scale(self.slider_frame, from_=1, to=5, orient='horizontal', resolution=0.01, variable=var, length=200, command=lambda e=None: self.slider_update_callback())
            scale.grid(row=row, column=2, padx=5)
            if 'upgrade' in model and not self.model_states.get(model['upgrade'], False):
                btn = tk.Button(self.slider_frame, text="Upgrade", command=lambda m=m: self.toggle_upgrade(m, upgrade=True), width=10)
                btn.grid(row=row, column=3, padx=5)
                self.upgrade_buttons[m] = btn
            elif 'downgrade' in model and not self.model_states.get(model['downgrade'], False):
                btn = tk.Button(self.slider_frame, text="Downgrade", command=lambda m=m: self.toggle_upgrade(m, upgrade=False), width=10)
                btn.grid(row=row, column=3, padx=5)
                self.upgrade_buttons[m] = btn
            row += 1


    def toggle_upgrade(self, m, upgrade=True):
        # Only one upgrade or downgrade per family, swap in-place
        if upgrade and 'upgrade' in MODEL_DEFS[m]:
            self.model_states[m] = False
            upg = MODEL_DEFS[m]['upgrade']
            self.model_states[upg] = True
            self.just_upgraded = upg
        elif not upgrade and 'downgrade' in MODEL_DEFS[m]:
            self.model_states[m] = False
            dng = MODEL_DEFS[m]['downgrade']
            self.model_states[dng] = True
            self.just_upgraded = dng
        self.update_model_sliders()


    def on_report_emp_select(self, event=None):
        emp_name_id = self.report_emp_var.get()
        emp = next((e for e in self.employees if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            return
        emp_id = emp['Employee ID']
        scores = self.employee_scores.get(emp_id, {})
        for m in self.slider_vars:
            if m in scores:
                self.slider_vars[m].set(scores[m])
            else:
                self.slider_vars[m].set(3)
        self.live_update_report()


    def live_update_report(self):
        self.update_risk_gradient()
        emp_name_id = self.report_emp_var.get()
        emp = next((e for e in self.employees if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            for w in self.report_output_frame.winfo_children():
                w.destroy()
            return
        emp_id = emp['Employee ID']
        # Save scores
        for m, var in self.slider_vars.items():
            self.employee_scores[emp_id][m] = var.get()
        # Calculate risk
        scores = [v for m, v in self.employee_scores[emp_id].items() if self.model_states.get(m, False)]
        if not scores:
            risk_score = 1
        else:
            risk_score = np.mean(scores)
        # Remove old gradient and percentage from report output (handled by always-visible gradient)
        for w in self.report_output_frame.winfo_children():
            w.destroy()
        # Recommendations
        recs = self.generate_recommendations(emp_id)
        tk.Label(self.report_output_frame, text="HR Recommendations:", font=('Arial', 14, 'bold')).pack(anchor='w', pady=5)
        for rec in recs:
            tk.Label(self.report_output_frame, text=f"• {rec}", wraplength=800, justify='left').pack(anchor='w')


    def generate_recommendations(self, emp_id):
        scores = self.employee_scores.get(emp_id, {})
        recs = []
        for m, v in scores.items():
            if v > 3.5:
                if m == 'burnout_olbi':
                    recs.append("High burnout detected: Consider wellness programs, workload reduction, and stress management.")
                    if 'upgrade' in MODEL_DEFS[m]:
                        recs.append(f"Upgrade to {MODEL_DEFS[m]['upgrade_name']} ({MODEL_DEFS[m]['upgrade_author']}) for more detail.")
                elif m == 'job_satisfaction_moaq':
                    recs.append("Low job satisfaction: Review compensation, work environment, and career development.")
                    if 'upgrade' in MODEL_DEFS[m]:
                        recs.append(f"Upgrade to {MODEL_DEFS[m]['upgrade_name']} ({MODEL_DEFS[m]['upgrade_author']}) for more detail.")
                elif m == 'job_embeddedness':
                    recs.append("Low job embeddedness: Build stronger organizational/community ties.")
                    if 'upgrade' in MODEL_DEFS[m]:
                        recs.append(f"Upgrade to {MODEL_DEFS[m]['upgrade_name']} ({MODEL_DEFS[m]['upgrade_author']}) for more detail.")
                elif m == 'perceived_organizational_support':
                    recs.append("Low perceived organizational support: Improve communication, recognition, and employee care.")
                elif m == 'psychological_safety':
                    recs.append("Low psychological safety: Implement team building, open communication, and leadership training.")
                elif m == 'work_engagement':
                    recs.append("Low work engagement: Focus on meaningful work, autonomy, and growth opportunities.")
        if not recs:
            recs.append("Overall risk is manageable. Continue monitoring and maintain positive practices.")
        return recs


    def create_report(self):
        emp_name_id = self.report_emp_var.get()
        emp = next((e for e in self.employees if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            return
        emp_id = emp['Employee ID']
        scores = self.employee_scores.get(emp_id, {})
        for m, var in self.slider_vars.items():
            self.employee_scores[emp_id][m] = var.get()
        scores = [v for v in self.employee_scores[emp_id].values()]
        if not scores:
            risk_score = 1
        else:
            risk_score = np.mean(scores)
        if risk_score <= 2.5:
            risk_level = "Low"
            risk_color = "#27ae60"
            risk_pct = int((risk_score/2.5)*30)
        elif risk_score <= 3.5:
            risk_level = "Moderate"
            risk_color = "#f39c12"
            risk_pct = int(30+((risk_score-2.5)/1.0)*40)
        else:
            risk_level = "High"
            risk_color = "#e74c3c"
            risk_pct = int(70+((risk_score-3.5)/1.5)*30)
        for w in self.report_output_frame.winfo_children():
            w.destroy()
        tk.Label(self.report_output_frame, text=f"Attrition Risk: {risk_pct}%", font=('Arial', 16, 'bold')).pack(pady=5)
        grad_fig, grad_ax = plt.subplots(figsize=(6,1))
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list('risk', ['#27ae60', '#f39c12', '#e74c3c'])
        grad = np.linspace(0,1,256).reshape(1,-1)
        grad_ax.imshow(grad, aspect='auto', cmap=cmap, extent=(0,100,0,1))
        grad_ax.axvline(risk_pct, color='black', lw=3)
        grad_ax.set_yticks([])
        grad_ax.set_xticks([0,25,50,75,100])
        grad_ax.set_xlabel('Risk (%)')
        grad_ax.set_title('Attrition Risk Gradient')
        grad_canvas = FigureCanvasTkAgg(grad_fig, master=self.report_output_frame)
        grad_canvas.draw()
        grad_canvas.get_tk_widget().pack(pady=5)
        plt.close(grad_fig)
        recs = self.generate_recommendations(emp_id)
        tk.Label(self.report_output_frame, text="HR Recommendations:", font=('Arial', 14, 'bold')).pack(anchor='w', pady=5)
        for rec in recs:
            tk.Label(self.report_output_frame, text=f"• {rec}", wraplength=800, justify='left').pack(anchor='w')


    def save_employee_data(self):
        emp_name_id = self.report_emp_var.get()
        emp = next((e for e in self.employees if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            return
        emp_id = emp['Employee ID']
        for m, var in self.slider_vars.items():
            self.employee_scores[emp_id][m] = var.get()
        scores = [v for v in self.employee_scores[emp_id].values()]
        if not scores:
            risk_score = 1
        else:
            risk_score = np.mean(scores)
        if risk_score <= 2.5:
            risk_level = "Low"
            risk_color = "#27ae60"
            risk_pct = int((risk_score/2.5)*30)
        elif risk_score <= 3.5:
            risk_level = "Moderate"
            risk_color = "#f39c12"
            risk_pct = int(30+((risk_score-2.5)/1.0)*40)
        else:
            risk_level = "High"
            risk_color = "#e74c3c"
            risk_pct = int(70+((risk_score-3.5)/1.5)*30)
        for w in self.report_output_frame.winfo_children():
            w.destroy()
        tk.Label(self.report_output_frame, text=f"Attrition Risk: {risk_pct}%", font=('Arial', 16, 'bold')).pack(pady=5)
        grad_fig, grad_ax = plt.subplots(figsize=(6,1))
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list('risk', ['#27ae60', '#f39c12', '#e74c3c'])
        grad = np.linspace(0,1,256).reshape(1,-1)
        grad_ax.imshow(grad, aspect='auto', cmap=cmap, extent=(0,100,0,1))
        grad_ax.axvline(risk_pct, color='black', lw=3)
        grad_ax.set_yticks([])
        grad_ax.set_xticks([0,25,50,75,100])
        grad_ax.set_xlabel('Risk (%)')
        grad_ax.set_title('Attrition Risk Gradient')
        grad_canvas = FigureCanvasTkAgg(grad_fig, master=self.report_output_frame)
        grad_canvas.draw()
        grad_canvas.get_tk_widget().pack(pady=5)
        plt.close(grad_fig)
        recs = self.generate_recommendations(emp_id)
        tk.Label(self.report_output_frame, text="HR Recommendations:", font=('Arial', 14, 'bold')).pack(anchor='w', pady=5)
        for rec in recs:
            tk.Label(self.report_output_frame, text=f"• {rec}", wraplength=800, justify='left').pack(anchor='w')


    def show_optional_models_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Optional Models")
        popup.geometry("300x300")
        tk.Label(popup, text="Select Optional Models:", font=("Segoe UI", 12, "bold")).pack(pady=10)
        opt_vars = {}
        for m in OPTIONAL_MODELS:
            var = tk.BooleanVar(value=self.model_states.get(m, False))
            opt_vars[m] = var
            tk.Checkbutton(popup, text=MODEL_DEFS[m]['name'], variable=var).pack(anchor='w', padx=20)
        def apply():
            for m in OPTIONAL_MODELS:
                if opt_vars[m].get():
                    self.model_states[m] = True
                else:
                    if m in self.model_states:
                        del self.model_states[m]
            self.update_model_sliders()
            self.slider_update_callback()
            popup.destroy()
        def back():
            popup.destroy()
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Apply", command=apply).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Back", command=back).pack(side='left', padx=10)


    def on_flag_single_left(self, event):
        rowid = self.emp_table.identify_row(event.y)
        if not rowid:
            return
        values = self.emp_table.item(rowid, 'values')
        if len(values) < 3:
            return
        emp_id = values[2]
        self.flag_status[emp_id] = 'flag'
        self.update_emp_table()


    def on_flag_double_left(self, event):
        rowid = self.emp_table.identify_row(event.y)
        if not rowid:
            return
        values = self.emp_table.item(rowid, 'values')
        if len(values) < 3:
            return
        emp_id = values[2]
        self.flag_status[emp_id] = 'hazard'
        self.update_emp_table()


    def on_flag_single_right(self, event):
        rowid = self.emp_table.identify_row(event.y)
        if not rowid:
            return
        values = self.emp_table.item(rowid, 'values')
        if len(values) < 3:
            return
        emp_id = values[2]
        self.flag_status[emp_id] = 'tick'
        self.update_emp_table()


    def on_flag_double_right(self, event):
        rowid = self.emp_table.identify_row(event.y)
        if not rowid:
            return
        values = self.emp_table.item(rowid, 'values')
        if len(values) < 3:
            return
        emp_id = values[2]
        self.flag_status[emp_id] = ''
        self.update_emp_table()


    def show_gemini_summary(self):
        """Show Gemini API summary in a popup"""
        emp_name_id = self.report_emp_var.get()
        emp = next((e for e in self.employees if f"{e['Name']} ({e['Employee ID']})" == emp_name_id), None)
        if not emp:
            messagebox.showwarning("Warning", "Please select an employee first")
            return
        
        # Show loading message
        popup = tk.Toplevel(self.root)
        popup.title("AI Summary")
        popup.geometry("600x400")
        popup.configure(bg='#e3f6fd')
        
        loading_label = tk.Label(popup, text="Generating AI summary...", font=("Segoe UI", 12), bg='#e3f6fd')
        loading_label.pack(pady=20)
        
        def generate_summary():
            summary = self.get_gemini_summary(emp['Employee ID'])
            popup.after(0, lambda: show_summary(summary))
        
        def show_summary(summary):
            loading_label.destroy()
            text_widget = tk.Text(popup, wrap='word', font=("Segoe UI", 11), bg='white', padx=10, pady=10)
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            text_widget.insert('1.0', summary)
            text_widget.config(state='disabled')
        
        # Run API call in separate thread
        thread = threading.Thread(target=generate_summary)
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    print("About to start mainloop")
    root = tk.Tk()
    app = AttritionApp(root)
    print("App created, entering mainloop")
    root.mainloop()
    print("Exited mainloop")

