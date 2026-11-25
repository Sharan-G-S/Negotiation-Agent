#!/usr/bin/env python3
"""
Launch script for NegoBotAI Web Application
Complete negotiation system with product search and NLP chat
"""

import sys
import os
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'jinja2',
        'websockets',
        'google-generativeai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   • {package}")
        print("\nInstall with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def launch_webapp():
    """Launch the complete web application"""
    print("🚀 Launching NegoBotAI Web Application...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print("Features:")
    print("  • Product Search & Discovery")
    print("  • Seller Comparison & Analysis") 
    print("  • AI-Powered Negotiation Chat")
    print("  • Real-time Price Tracking")
    print("  • Deal Analytics & History")
    print()
    
    if not check_requirements():
        return
    
    # Set environment variables
    os.environ.setdefault('GOOGLE_API_KEY', '')
    
    # Launch the web application
    try:
        from new_agent.main import main
        sys.argv = ['launch_webapp.py', 'webapp']
        main()
    except Exception as e:
        print(f"❌ Error launching web app: {e}")
        print("\nTrying alternative launch method...")
        try:
            subprocess.run([sys.executable, '-m', 'new_agent.main', 'webapp'])
        except Exception as e2:
            print(f"❌ Alternative launch failed: {e2}")
            print("\nManual launch:")
            print("   python -m new_agent.main webapp")

if __name__ == "__main__":
    launch_webapp()