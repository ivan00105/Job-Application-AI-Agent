"""
Test script demonstrating various filter options for job search.
Shows how to use company filters, experience filters, certifications, etc.

Usage:
    python backend/scripts/jobs-finder/test_search_with_filters.py
"""
import requests
import json
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SEARCH_ENDPOINT = f"{API_BASE_URL}/api/jobs/search"

TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser1")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password123")


def get_token():
    """Get authentication token."""
    response = requests.post(
        f"{API_BASE_URL}/api/auth/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        timeout=10
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def search_with_filters(query: str, token: str, **filters):
    """Perform search with filters."""
    payload = {
        "query": query,
        "limit": 10,
        **filters
    }
    
    response = requests.post(
        SEARCH_ENDPOINT,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def main():
    print("=" * 80)
    print("JOB SEARCH WITH FILTERS - DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Authenticate
    print("Authenticating...")
    token = get_token()
    if not token:
        print("ERROR: Authentication failed")
        return
    print("OK: Authenticated\n")
    
    # Example 1: Search with company filter
    print("Example 1: Search 'engineer' at specific company")
    print("-" * 80)
    data = search_with_filters(
        "engineer",
        token,
        company_filter="Google"  # Adjust based on your data
    )
    if data:
        print(f"Found {data['count']} results\n")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"{i}. {payload.get('job_title')} at {payload.get('company')}")
    print()
    
    # Example 2: Search with experience requirement
    print("Example 2: Search 'developer' with 3+ years experience")
    print("-" * 80)
    data = search_with_filters(
        "developer",
        token,
        min_experience_years=3
    )
    if data:
        print(f"Found {data['count']} results\n")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"{i}. {payload.get('job_title')} - Score: {result['score']:.4f}")
    print()
    
    # Example 3: Search with certifications
    print("Example 3: Search 'cloud' jobs requiring AWS certification")
    print("-" * 80)
    data = search_with_filters(
        "cloud",
        token,
        certifications=["AWS"]
    )
    if data:
        print(f"Found {data['count']} results\n")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"{i}. {payload.get('job_title')} at {payload.get('company')}")
    print()
    
    # Example 4: Combined filters
    print("Example 4: Combined filters - 'backend' with experience + certifications")
    print("-" * 80)
    data = search_with_filters(
        "backend",
        token,
        min_experience_years=2,
        certifications=["Python", "Django"],
        use_llm_enhancement=True
    )
    if data:
        print(f"Found {data['count']} results\n")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"{i}. {payload.get('job_title')} at {payload.get('company')}")
    print()
    
    # Example 5: High similarity threshold
    print("Example 5: Search with high similarity threshold (0.8)")
    print("-" * 80)
    data = search_with_filters(
        "machine learning engineer",
        token,
        score_threshold=0.8
    )
    if data:
        print(f"Found {data['count']} results (only highly similar matches)\n")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"{i}. {payload.get('job_title')} - Score: {result['score']:.4f}")
    print()
    
    print("=" * 80)
    print("Done!")
    print("=" * 80)


if __name__ == "__main__":
    main()

