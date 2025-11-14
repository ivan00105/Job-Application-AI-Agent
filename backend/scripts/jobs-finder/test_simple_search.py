"""
Simple test script for quick job search API testing.
This is a minimal script for quick testing without running the full test suite.

Usage:
    python backend/scripts/jobs-finder/test_simple_search.py "your search query"

Example:
    python backend/scripts/jobs-finder/test_simple_search.py "Python developer"
"""
import requests
import json
import sys
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SEARCH_ENDPOINT = f"{API_BASE_URL}/api/jobs/search"

# Test user credentials
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser1")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password123")


def main():
    # Get search query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Python developer"
    
    print(f"🔍 Testing job search API")
    print(f"Query: {query}\n")
    
    # Step 1: Authenticate
    print("1. Authenticating...")
    try:
        auth_response = requests.post(
            f"{API_BASE_URL}/api/auth/token",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(f"   {auth_response.text}")
            return
        
        token = auth_response.json().get("access_token")
        print("✅ Authenticated\n")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running on http://localhost:8000?")
        return
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    
    # Step 2: Perform search
    print("2. Searching jobs...")
    try:
        search_payload = {
            "query": query,
            "limit": 10,
            "use_llm_enhancement": True
        }
        
        response = requests.post(
            SEARCH_ENDPOINT,
            json=search_payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   {response.text}")
            return
        
        data = response.json()
        count = data.get("count", 0)
        results = data.get("results", [])
        
        print(f"✅ Found {count} results\n")
        
        if not results:
            print("No results found.")
            return
        
        # Display results
        print("Results:")
        print("-" * 80)
        for i, result in enumerate(results[:5], 1):
            payload = result.get("payload", {})
            score = result.get("score", 0)
            
            print(f"\n{i}. {payload.get('job_title', 'N/A')}")
            print(f"   Company: {payload.get('company', 'N/A')}")
            print(f"   Location: {payload.get('location', 'N/A')}")
            print(f"   Score: {score:.4f}")
            
            # Show URL if available
            url = payload.get('url') or payload.get('job_url')
            if url:
                print(f"   URL: {url}")
        
        print("\n" + "-" * 80)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

