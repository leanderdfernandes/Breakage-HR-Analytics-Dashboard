#!/usr/bin/env python3
"""
Breakage - Attrition Risk Detector Launcher
Professional HR Analytics Dashboard
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit application"""
    print("🚀 Starting Breakage - Professional Attrition Risk Detector")
    print("=" * 60)
    
    # Check if required files exist
    required_files = [
        "streamlit_app_enhanced.py",
        "employee_data.csv",
        "employee_data_enhanced.csv"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all required files are in the current directory.")
        return
    
    print("✅ All required files found")
    print("📊 Launching Streamlit application...")
    print("🌐 The application will open in your default browser")
    print("🔗 URL: http://localhost:8501")
    print("=" * 60)
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app_enhanced.py",
            "--server.port", "8501",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")

if __name__ == "__main__":
    main() 