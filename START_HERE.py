#!/usr/bin/env python3
"""
Power BI Testing Tool - FIXED VERSION LAUNCHER

This runs the SIMPLE, FIXED version that works correctly.
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 Power BI Testing Tool - FIXED VERSION")
    print("=" * 60)
    print("✅ Using SIMPLE version (not complex version)")
    print("✅ File selection issues FIXED")
    print("✅ Method errors FIXED")
    print("=" * 60)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    try:
        import flask
        print("   ✅ Flask installed")
        import werkzeug
        print("   ✅ Werkzeug installed")
    except ImportError as e:
        print(f"   ❌ Missing: {e}")
        print("\n🔧 Install with: pip install -r requirements.txt")
        return 1
    
    print("   🎉 All dependencies OK!")
    print()
    
    # Set up directories
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Ensure directories exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Import the FIXED simple version
    print("📱 Starting web server...")
    try:
        from simple_web_app import app
        
        print("🌐 Open browser: http://localhost:5000")
        print("📁 Drag & drop .pbix files")
        print("⚡ Get instant analysis!")
        print()
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Stopped. Thanks for using the tool!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 