"""
Test script to get recommended jobs for testuser2.
This tests the /api/jobs/recommended endpoint which uses CV profile and saved jobs.
"""
import requests
import os
import sys
import json

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USERNAME = "testuser2"
TEST_PASSWORD = "password123"


def main():
    print("=" * 70)
    print("TEST RECOMMENDED JOBS FOR TESTUSER2")
    print("=" * 70)
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
    
    # Step 2: Authenticate as testuser2
    print(f"2. Authenticating as {TEST_USERNAME}...")
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
    
    # Step 3: Check user profile
    print("3. Checking user profile...")
    try:
        profile_response = requests.get(
            f"{API_BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if profile_response.status_code == 200:
            user_data = profile_response.json()
            print(f"   ✅ User: {user_data.get('username', 'N/A')}")
            print(f"   User ID: {user_data.get('id', 'N/A')}")
        else:
            print(f"   ⚠️  Could not get user profile: {profile_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error getting profile: {str(e)}")
    
    print()
    
    # Step 4: Check CV profile
    print("4. Checking CV profile...")
    try:
        cv_response = requests.get(
            f"{API_BASE_URL}/api/cv/profile",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if cv_response.status_code == 200:
            cv_data = cv_response.json()
            print("   ✅ CV profile exists")
            parsed_data = cv_data.get("parsed_data", {})
            if isinstance(parsed_data, dict):
                skills = parsed_data.get("skills", {})
                if isinstance(skills, dict):
                    technical = skills.get("technical", [])
                    if technical:
                        print(f"   Skills: {', '.join(technical[:5])}")
                experiences = parsed_data.get("experiences", [])
                if experiences:
                    print(f"   Experiences: {len(experiences)} position(s)")
        elif cv_response.status_code == 404:
            print("   ⚠️  No CV profile found")
            print("   Recommendations will use saved jobs or latest jobs")
        else:
            print(f"   ⚠️  Unexpected response: {cv_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error checking CV: {str(e)}")
    
    print()
    
    # Step 5: Check saved jobs
    print("5. Checking saved jobs...")
    try:
        apps_response = requests.get(
            f"{API_BASE_URL}/api/applications/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if apps_response.status_code == 200:
            apps_data = apps_response.json()
            saved_count = len([app for app in apps_data.get("applications", []) 
                             if app.get("status") in ["saved", "applied", "interviewing"]])
            print(f"   Found {saved_count} saved/applied job(s)")
            if saved_count > 0:
                for app in apps_data.get("applications", [])[:3]:
                    if app.get("status") in ["saved", "applied", "interviewing"]:
                        job = app.get("job", {})
                        print(f"   - {job.get('title', 'N/A')} at {job.get('company', 'N/A')} ({app.get('status')})")
        else:
            print(f"   ⚠️  Could not get applications: {apps_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error checking saved jobs: {str(e)}")
    
    print()
    
    # Step 6: Get recommended jobs
    print("6. Getting recommended jobs...")
    try:
        recommended_response = requests.get(
            f"{API_BASE_URL}/api/jobs/recommended",
            params={"limit": 10, "offset": 0},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if recommended_response.status_code == 200:
            data = recommended_response.json()
            jobs = data.get("jobs", [])
            total = data.get("total", 0)
            source = data.get("source", "unknown")
            
            print(f"   ✅ Recommendations retrieved!")
            print(f"   Source: {source}")
            if source == "latest":
                print("   ⚠️  Using latest jobs (fallback)")
                print("   This means CV vector search or saved jobs search didn't work")
                print("   Possible reasons:")
                print("   - Vector search services (Qdrant/Ollama) unavailable")
                print("   - CV profile data not suitable for vector search")
                print("   - No matching jobs found in vector search")
            elif source == "cv_vector_search":
                print("   ✅ Using CV profile for vector search")
            elif source == "similar_to_saved":
                print("   ✅ Using saved jobs for similar job search")
            elif source == "cv_matches":
                print("   ✅ Using pre-calculated CV matches")
            print(f"   Total jobs: {total}")
            print(f"   Jobs returned: {len(jobs)}")
            print()
            
            if jobs:
                print("   Recommended Jobs:")
                print("   " + "-" * 66)
                for i, job in enumerate(jobs[:10], 1):
                    title = job.get("title", "N/A")
                    company = job.get("company", "N/A")
                    location = job.get("location", "N/A")
                    applied = job.get("applied", False)
                    status = job.get("application_status", "")
                    
                    applied_text = f" [APPLIED: {status}]" if applied else ""
                    
                    print(f"   {i}. {title}")
                    print(f"      Company: {company}")
                    print(f"      Location: {location}{applied_text}")
                    
                    # Show score if available (from job_matches)
                    if "overall_score" in job:
                        print(f"      Match Score: {job.get('overall_score', 0):.4f}")
                    
                    print()
            else:
                print("   ⚠️  No recommended jobs found")
                print("   This might mean:")
                print("   - No jobs in database")
                print("   - No CV profile and no saved jobs")
                print("   - Vector search services unavailable")
            
            return True
        else:
            print(f"   ❌ Failed to get recommendations: {recommended_response.status_code}")
            print(f"   Response: {recommended_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    print()
    print("=" * 70)
    if success:
        print("✅ Test completed!")
    else:
        print("❌ Test failed")
    print("=" * 70)
    sys.exit(0 if success else 1)

