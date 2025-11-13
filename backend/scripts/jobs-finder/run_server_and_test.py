"""
Script to start the server and run the job search API test.
This script will:
1. Start the uvicorn server in a subprocess
2. Wait for it to be ready
3. Run the quick test
4. Clean up the server process
"""
import subprocess
import sys
import time
import requests
import os
import signal
import atexit

# Change to backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
os.chdir(backend_dir)

API_BASE_URL = "http://localhost:8000"
server_process = None

def cleanup():
    """Clean up server process on exit"""
    global server_process
    if server_process:
        try:
            print("\nShutting down server...")
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            try:
                server_process.kill()
            except:
                pass

atexit.register(cleanup)

def check_server_ready(max_attempts=30, delay=1):
    """Check if server is ready"""
    for i in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(delay)
    return False

def main():
    global server_process
    
    print("=" * 70)
    print("Job Search API - Starting Server and Running Test")
    print("=" * 70)
    print()
    
    # Check if server is already running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is already running!")
            print()
            # Run test
            from quick_test import main as test_main
            return test_main()
    except:
        pass
    
    # Start server
    print("1. Starting server...")
    try:
        server_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=backend_dir
        )
        print("   Server process started (PID: {})".format(server_process.pid))
    except Exception as e:
        print(f"   ❌ Failed to start server: {str(e)}")
        return False
    
    print()
    print("2. Waiting for server to be ready...")
    if check_server_ready():
        print("   ✅ Server is ready!")
    else:
        print("   ❌ Server failed to start within timeout period")
        cleanup()
        return False
    
    print()
    print("3. Running job search API test...")
    print("-" * 70)
    print()
    
    # Import and run the quick test
    sys.path.insert(0, os.path.join(backend_dir, "scripts", "jobs-finder"))
    from quick_test import main as test_main
    
    try:
        result = test_main()
        return result
    except Exception as e:
        print(f"   ❌ Test failed with error: {str(e)}")
        return False
    finally:
        print()
        print("4. Cleaning up...")
        cleanup()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        cleanup()
        sys.exit(1)

