"""
Script to start the server and run tests.
Note: This requires the server to be started manually in a separate terminal first.
"""
import subprocess
import sys
import time
import requests
import os

def check_server_running():
    """Check if server is already running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("=" * 60)
    print("Job Search API - Server Check and Test")
    print("=" * 60)
    print()
    
    if check_server_running():
        print("✅ Server is already running!")
        print()
    else:
        print("❌ Server is not running.")
        print()
        print("Please start the server in a separate terminal:")
        print("  cd backend")
        print("  python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        print()
        print("Then run this script again, or run:")
        print("  python backend/scripts/jobs-finder/quick_test.py")
        print()
        return False
    
    # Run the quick test
    print("Running job search API test...")
    print("-" * 60)
    print()
    
    # Import and run the quick test
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from scripts.jobs_finder.quick_test import main as test_main
    
    return test_main()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

