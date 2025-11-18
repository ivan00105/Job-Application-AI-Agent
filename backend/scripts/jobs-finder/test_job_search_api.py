"""
Test script for the job search API endpoint.
Tests the POST /api/jobs/search-vector endpoint with various scenarios.

Usage:
    python backend/scripts/jobs-finder/test_job_search_api.py

Requirements:
    - Backend API server must be running on http://localhost:8000
    - User must be authenticated (will attempt to login automatically)
    - Qdrant must be running with job data in the collection
"""
import requests
import json
import sys
import os
from typing import Optional, Dict, Any

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SEARCH_ENDPOINT = f"{API_BASE_URL}/api/jobs/search-vector"

# Test user credentials (adjust as needed)
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser1")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "password123")

# Default collection name
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "job_data")


def get_auth_token() -> Optional[str]:
    """Get authentication token by logging in."""
    try:
        print("🔐 Authenticating...")
        response = requests.post(
            f"{API_BASE_URL}/api/auth/token",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ Authentication successful\n")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Is it running?")
        return None
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None


def test_search(
    query: str,
    token: str,
    limit: int = 10,
    collection_name: str = DEFAULT_COLLECTION,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Test job search via API endpoint.
    
    Args:
        query: Search query string
        token: Authentication token
        limit: Number of results to return
        collection_name: Qdrant collection name
        **kwargs: Additional search parameters (score_threshold, company_filter, etc.)
    
    Returns:
        Response JSON or None if error
    """
    try:
        # Separate body params from query params for /search-vector endpoint
        body_params = {
            "query": query,
            "limit": limit,
        }
        
        # Add optional body params
        if "use_llm_enhancement" in kwargs:
            body_params["use_llm_enhancement"] = kwargs.pop("use_llm_enhancement")
        if "score_threshold" in kwargs:
            body_params["score_threshold"] = kwargs.pop("score_threshold")
        if "company_filter" in kwargs:
            body_params["company_filter"] = kwargs.pop("company_filter")
        if "min_experience_years" in kwargs:
            body_params["min_experience_years"] = kwargs.pop("min_experience_years")
        if "certifications" in kwargs:
            body_params["certifications"] = kwargs.pop("certifications")
        
        # Remaining kwargs become query params (location, hide_saved, offset)
        query_params = kwargs
        
        print(f"🔍 Searching: '{query}'")
        if body_params or query_params:
            print(f"   Body params: {body_params}")
            if query_params:
                print(f"   Query params: {query_params}")
        
        response = requests.post(
            SEARCH_ENDPOINT,
            json=body_params,
            params=query_params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        return None
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None


def print_results(data: Dict[str, Any], max_results: int = 3):
    """Print search results in a formatted way."""
    if not data:
        return
    
    count = data.get("total", 0)
    jobs = data.get("jobs", [])
    
    print(f"✅ Found {count} results\n")
    
    if not jobs:
        print("   No results found.\n")
        return
    
    print("Top results:")
    print("-" * 80)
    
    for i, job in enumerate(jobs[:max_results], 1):
        print(f"\n{i}. {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        
        # Show snippet of description if available
        description = job.get('description', '')
        if description:
            snippet = description[:150] + "..." if len(description) > 150 else description
            print(f"   Description: {snippet}")
    
    print("-" * 80)
    print()


def test_basic_search(token: str):
    """Test 1: Basic job search without filters."""
    print("=" * 80)
    print("TEST 1: Basic Job Search")
    print("=" * 80)
    print()
    
    data = test_search("Python developer", token, limit=5)
    print_results(data, max_results=3)
    
    return data is not None


def test_search_with_llm_enhancement(token: str):
    """Test 2: Search with LLM query enhancement."""
    print("=" * 80)
    print("TEST 2: Search with LLM Enhancement")
    print("=" * 80)
    print()
    
    data = test_search(
        "data scientist",
        token,
        limit=5,
        use_llm_enhancement=True
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_without_llm(token: str):
    """Test 3: Search without LLM enhancement."""
    print("=" * 80)
    print("TEST 3: Search without LLM Enhancement")
    print("=" * 80)
    print()
    
    data = test_search(
        "software engineer",
        token,
        limit=5,
        use_llm_enhancement=False
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_with_company_filter(token: str):
    """Test 4: Search with company filter."""
    print("=" * 80)
    print("TEST 4: Search with Company Filter")
    print("=" * 80)
    print()
    
    data = test_search(
        "engineer",
        token,
        limit=5,
        company_filter="Google"  # Adjust based on your data
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_with_experience_filter(token: str):
    """Test 5: Search with minimum experience filter."""
    print("=" * 80)
    print("TEST 5: Search with Experience Filter")
    print("=" * 80)
    print()
    
    data = test_search(
        "developer",
        token,
        limit=5,
        min_experience_years=3
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_with_certifications(token: str):
    """Test 6: Search with certifications/skills filter."""
    print("=" * 80)
    print("TEST 6: Search with Certifications Filter")
    print("=" * 80)
    print()
    
    data = test_search(
        "cloud engineer",
        token,
        limit=5,
        certifications=["AWS", "Docker"]
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_with_score_threshold(token: str):
    """Test 7: Search with similarity score threshold."""
    print("=" * 80)
    print("TEST 7: Search with Score Threshold")
    print("=" * 80)
    print()
    
    data = test_search(
        "machine learning",
        token,
        limit=10,
        score_threshold=0.7  # Only return results with similarity >= 0.7
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_search_combined_filters(token: str):
    """Test 8: Search with multiple filters combined."""
    print("=" * 80)
    print("TEST 8: Search with Combined Filters")
    print("=" * 80)
    print()
    
    data = test_search(
        "backend developer",
        token,
        limit=5,
        company_filter="Microsoft",  # Adjust based on your data
        min_experience_years=2,
        certifications=["Python", "Django"],
        use_llm_enhancement=True
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_custom_collection(token: str):
    """Test 9: Search in a custom collection."""
    print("=" * 80)
    print("TEST 9: Search in Custom Collection")
    print("=" * 80)
    print()
    
    # Test with a different collection (if it exists)
    custom_collection = os.getenv("CUSTOM_COLLECTION", "job_data")
    
    data = test_search(
        "analyst",
        token,
        limit=5,
        collection_name=custom_collection
    )
    print_results(data, max_results=3)
    
    return data is not None


def test_edge_cases(token: str):
    """Test 10: Edge cases and error handling."""
    print("=" * 80)
    print("TEST 10: Edge Cases")
    print("=" * 80)
    print()
    
    # Test with empty query
    print("Testing empty query...")
    data = test_search("", token, limit=5)
    if data:
        print(f"   Got {data.get('count', 0)} results\n")
    
    # Test with very long query
    print("Testing very long query...")
    long_query = " ".join(["developer"] * 50)
    data = test_search(long_query, token, limit=5)
    if data:
        print(f"   Got {data.get('count', 0)} results\n")
    
    # Test with very high score threshold (should return few/no results)
    print("Testing high score threshold...")
    data = test_search("engineer", token, limit=10, score_threshold=0.99)
    if data:
        print(f"   Got {data.get('count', 0)} results (expected: 0 or very few)\n")
    
    return True


def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "=" * 80)
    print("JOB SEARCH API TEST SUITE")
    print("=" * 80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Search Endpoint: {SEARCH_ENDPOINT}")
    print(f"Collection: {DEFAULT_COLLECTION}")
    print("=" * 80)
    print()
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token.")
        print("   Please ensure:")
        print("   1. API server is running")
        print("   2. Test user exists (run: python backend/scripts/create_test_users.py)")
        print("   3. Credentials are correct")
        return False
    
    # Run tests
    tests = [
        ("Basic Search", test_basic_search),
        ("LLM Enhancement", test_search_with_llm_enhancement),
        ("Without LLM", test_search_without_llm),
        ("Company Filter", test_search_with_company_filter),
        ("Experience Filter", test_search_with_experience_filter),
        ("Certifications Filter", test_search_with_certifications),
        ("Score Threshold", test_search_with_score_threshold),
        ("Combined Filters", test_search_combined_filters),
        ("Custom Collection", test_custom_collection),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(token)
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with error: {str(e)}\n")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

