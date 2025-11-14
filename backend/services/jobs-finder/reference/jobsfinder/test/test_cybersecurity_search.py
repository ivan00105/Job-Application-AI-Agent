"""
Test script to demonstrate the cybersecurity job search API.
Run this after starting the API server.
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"
COLLECTION_NAME = "job_data"

def test_cybersecurity_search():
    """Test the cybersecurity job search endpoint."""
    print("=" * 60)
    print("Cybersecurity Job Search API Test")
    print("=" * 60)
    print()
    
    # Test 1: Basic cybersecurity search
    print("Test 1: Basic cybersecurity search (all cybersecurity jobs)")
    print("-" * 60)
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search/cybersecurity",
        json={
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} cybersecurity jobs")
        print(f"\nTop 3 results:")
        for i, result in enumerate(data['results'][:3], 1):
            payload = result['payload']
            print(f"\n  {i}. {payload.get('job_title', 'N/A')}")
            print(f"     Company: {payload.get('company', 'N/A')}")
            print(f"     Similarity Score: {result['score']:.4f}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "=" * 60)
    
    # Test 2: Search with specific query
    print("\nTest 2: Search for 'penetration testing' jobs")
    print("-" * 60)
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search/cybersecurity",
        json={
            "query": "penetration testing",
            "limit": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} jobs related to penetration testing")
        for i, result in enumerate(data['results'], 1):
            payload = result['payload']
            print(f"\n  {i}. {payload.get('job_title', 'N/A')} at {payload.get('company', 'N/A')}")
            print(f"     Score: {result['score']:.4f}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "=" * 60)
    
    # Test 3: Search with certification filter
    print("\nTest 3: Search for jobs requiring CISSP certification")
    print("-" * 60)
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search/cybersecurity",
        json={
            "certifications": ["CISSP"],
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} jobs requiring CISSP")
        for i, result in enumerate(data['results'], 1):
            payload = result['payload']
            print(f"\n  {i}. {payload.get('job_title', 'N/A')} at {payload.get('company', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "=" * 60)
    
    # Test 4: Search with experience filter
    print("\nTest 4: Search for jobs requiring 5+ years experience")
    print("-" * 60)
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search/cybersecurity",
        json={
            "min_experience_years": 5,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} jobs requiring 5+ years experience")
        for i, result in enumerate(data['results'], 1):
            payload = result['payload']
            print(f"\n  {i}. {payload.get('job_title', 'N/A')} at {payload.get('company', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "=" * 60)
    
    # Test 5: Combined filters
    print("\nTest 5: Search with multiple filters (CEH + 3+ years)")
    print("-" * 60)
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search/cybersecurity",
        json={
            "query": "security engineer",
            "certifications": ["CEH", "CISSP"],
            "min_experience_years": 3,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} jobs matching all criteria")
        for i, result in enumerate(data['results'], 1):
            payload = result['payload']
            print(f"\n  {i}. {payload.get('job_title', 'N/A')} at {payload.get('company', 'N/A')}")
            print(f"     Score: {result['score']:.4f}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "=" * 60)
    print("\n✅ All tests completed!")
    print("\nTo use the API, start the server with:")
    print("  uvicorn app.main:app --reload")
    print("\nThen access the interactive docs at:")
    print(f"  {API_BASE_URL}/docs")

if __name__ == "__main__":
    try:
        test_cybersecurity_search()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

