"""
Quick verification script to test if the job search API is working.
This is the simplest test - just checks if the endpoint is accessible and returns results.

Usage:
    python backend/scripts/jobs-finder/quick_test.py
"""
import requests
import os
import sys

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser1")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password123")


def main():
    print("=" * 60)
    print("QUICK JOB SEARCH API TEST")
    print("=" * 60)
    print()
    
    # Step 1: Check if server is running
    print("1. Checking if API server is running...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ⚠️  Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server")
        print(f"   Make sure the server is running on {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    print()
    
    # Step 2: Authenticate
    print("2. Authenticating...")
    try:
        auth_response = requests.post(
            f"{API_BASE_URL}/api/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=10
        )
        
        if auth_response.status_code != 200:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            print()
            print("   💡 Tip: Create test user with:")
            print("      python backend/scripts/create_test_users.py")
            return False
        
        token = auth_response.json().get("access_token")
        print("   ✅ Authentication successful")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    print()
    
    # Step 3: Test search
    print("3. Testing job search...")
    try:
        search_response = requests.post(
            f"{API_BASE_URL}/api/jobs/search",
            json={
                "query": "developer",
                "limit": 3
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if search_response.status_code == 200:
            data = search_response.json()
            count = data.get("count", 0)
            print(f"   ✅ Search successful!")
            print(f"   Found {count} results")
            
            if count > 0:
                print()
                print("   Sample result:")
                result = data["results"][0]
                payload = result.get("payload", {})
                print(f"   - Title: {payload.get('job_title', 'N/A')}")
                print(f"   - Company: {payload.get('company', 'N/A')}")
                print(f"   - Score: {result.get('score', 0):.4f}")
            else:
                print()
                print("   ⚠️  No results found")
                print("   This might mean:")
                print("   - Qdrant doesn't have job data yet")
                print("   - Collection name doesn't match")
                print("   - Try a different search query")
            
            return True
        else:
            print(f"   ❌ Search failed: {search_response.status_code}")
            print(f"   Response: {search_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    print()
    print("=" * 60)
    if success:
        print("✅ Quick test completed!")
        print()
        print("Next steps:")
        print("  - Run full test suite: python backend/scripts/jobs-finder/test_job_search_api.py")
        print("  - Try custom search: python backend/scripts/jobs-finder/test_simple_search.py 'your query'")
    else:
        print("❌ Quick test failed")
        print()
        print("Troubleshooting:")
        print("  1. Ensure backend server is running: python backend/main.py")
        print("  2. Create test user: python backend/scripts/create_test_users.py")
        print("  3. Check Qdrant is running and has data")
    print("=" * 60)
    sys.exit(0 if success else 1)

