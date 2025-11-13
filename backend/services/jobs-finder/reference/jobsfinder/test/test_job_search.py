"""
Comprehensive test script to search for jobs in the Qdrant database.
This script can test both via API (if server is running) or directly using services.
"""
import asyncio
import sys
import requests
from typing import Optional
from app.config import settings
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service

API_BASE_URL = "http://localhost:8000"
COLLECTION_NAME = "job_data"

def test_via_api(query: str, limit: int = 10) -> Optional[dict]:
    """Test job search via API endpoint."""
    try:
        print(f"🔍 Searching via API: '{query}'...")
        response = requests.post(
            f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search",
            json={
                "query": query,
                "limit": limit
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("⚠️  API server is not running. Trying direct service test...")
        return None
    except Exception as e:
        print(f"❌ API request failed: {str(e)}")
        return None

async def test_via_service(query: str, limit: int = 10) -> Optional[dict]:
    """Test job search directly using services."""
    try:
        print(f"🔍 Searching via direct service: '{query}'...")
        
        # Check if collection exists
        if not qdrant_service.collection_exists(COLLECTION_NAME):
            print(f"❌ Collection '{COLLECTION_NAME}' does not exist!")
            print(f"   Please import job data first using: python import_job_data.py")
            return None
        
        # Generate embedding for query
        query_vector = await embedding_service.generate_embedding(query)
        
        # Search in Qdrant
        results = qdrant_service.search_jobs(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit
        )
        
        return {
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def display_results(data: dict, query: str):
    """Display search results in a formatted way."""
    if not data or data.get('count', 0) == 0:
        print(f"\n❌ No jobs found for query: '{query}'")
        return
    
    print(f"\n{'='*80}")
    print(f"✅ Found {data['count']} job(s) for query: '{query}'")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(data['results'], 1):
        payload = result.get('payload', {})
        score = result.get('score', 0)
        
        print(f"{'─'*80}")
        print(f"Result #{i} (Similarity Score: {score:.4f})")
        print(f"{'─'*80}")
        print(f"📌 Job Title: {payload.get('job_title', 'N/A')}")
        print(f"🏢 Company: {payload.get('company', 'N/A')}")
        
        if payload.get('job_date'):
            print(f"📅 Date: {payload.get('job_date', 'N/A')}")
        
        # Show responsibilities
        responsibilities = payload.get('job_responsibilities', '')
        if responsibilities:
            print(f"\n📋 Responsibilities:")
            # Show first 300 characters
            snippet = responsibilities[:300].replace('\n', ' ')
            print(f"   {snippet}")
            if len(responsibilities) > 300:
                print(f"   ... (truncated)")
        
        # Show requirements
        requirements = payload.get('job_requirements', '')
        if requirements:
            print(f"\n✅ Requirements:")
            # Show first 300 characters
            snippet = requirements[:300].replace('\n', ' ')
            print(f"   {snippet}")
            if len(requirements) > 300:
                print(f"   ... (truncated)")
        
        # Show how to apply
        to_apply = payload.get('to_apply', '')
        if to_apply:
            print(f"\n📧 To Apply:")
            snippet = to_apply[:200].replace('\n', ' ')
            print(f"   {snippet}")
            if len(to_apply) > 200:
                print(f"   ... (truncated)")
        
        print()

async def test_multiple_queries():
    """Test multiple different job search queries."""
    test_queries = [
        "software engineer",
        "data analyst",
        "Python developer",
        "machine learning",
        "financial analyst",
        "cybersecurity",
        "project manager"
    ]
    
    print("="*80)
    print("Testing Multiple Job Search Queries")
    print("="*80)
    print()
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Testing Query: '{query}'")
        print(f"{'='*80}")
        
        # Try API first
        result = test_via_api(query, limit=5)
        
        # If API fails, try direct service
        if result is None:
            result = await test_via_service(query, limit=5)
        
        if result:
            display_results(result, query)
        else:
            print(f"❌ Could not search for '{query}'")
        
        print()

async def main():
    """Main test function."""
    print("="*80)
    print("Job Search Test Script")
    print("="*80)
    print()
    print("This script tests the job search functionality.")
    print("It will try to use the API first, then fall back to direct service calls.")
    print()
    
    # Check if collection exists (for direct service test)
    try:
        if qdrant_service.collection_exists(COLLECTION_NAME):
            info = qdrant_service.get_collection_info(COLLECTION_NAME)
            print(f"✅ Collection '{COLLECTION_NAME}' exists")
            print(f"   Points in collection: {info.get('points_count', 0)}")
        else:
            print(f"⚠️  Collection '{COLLECTION_NAME}' does not exist")
            print(f"   Please import job data first using: python import_job_data.py")
    except Exception as e:
        print(f"⚠️  Could not check collection: {str(e)}")
    
    print()
    
    # Test a single query first
    test_query = "software engineer"
    print(f"Testing single query: '{test_query}'")
    print("-"*80)
    
    # Try API first
    result = test_via_api(test_query, limit=10)
    
    # If API fails, try direct service
    if result is None:
        result = await test_via_service(test_query, limit=10)
    
    if result:
        display_results(result, test_query)
    else:
        print(f"\n❌ Test failed. Please check:")
        print(f"   1. Is Qdrant running?")
        print(f"   2. Is Ollama running with bge-m3 model?")
        print(f"   3. Is the collection '{COLLECTION_NAME}' created and populated?")
        print(f"   4. If using API, is the server running? (uvicorn app.main:app --reload)")
        return 1
    
    # Ask if user wants to test more queries
    print("\n" + "="*80)
    response = input("Do you want to test multiple queries? (yes/no): ").strip().lower()
    if response == 'yes':
        await test_multiple_queries()
    
    print("\n" + "="*80)
    print("✅ Test completed!")
    print("="*80)
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

