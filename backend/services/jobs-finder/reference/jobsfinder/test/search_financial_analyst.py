"""
Quick script to search for financial analyst jobs
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"
COLLECTION_NAME = "job_data"

def search_financial_analyst_jobs():
    """Search for financial analyst jobs."""
    print("=" * 70)
    print("Financial Analyst Jobs Search")
    print("=" * 70)
    print()
    
    # Search for financial analyst jobs
    response = requests.post(
        f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search",
        json={
            "query": "financial analyst",
            "limit": 15
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} financial analyst related jobs\n")
        print("-" * 70)
        
        for i, result in enumerate(data['results'], 1):
            payload = result['payload']
            print(f"\n{i}. {payload.get('job_title', 'N/A')}")
            print(f"   Company: {payload.get('company', 'N/A')}")
            print(f"   Similarity Score: {result['score']:.4f}")
            print(f"   Date: {payload.get('job_date', 'N/A')}")
            
            # Show a snippet of requirements if available
            requirements = payload.get('job_requirements', '')
            if requirements:
                # Get first 200 characters
                snippet = requirements[:200].replace('\n', ' ')
                if len(requirements) > 200:
                    snippet += "..."
                print(f"   Requirements: {snippet}")
            
            print("-" * 70)
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        search_financial_analyst_jobs()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

