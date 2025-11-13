"""
Test script for enhanced job search with structured filtering.
Tests the generic search endpoint with LLM enhancement and filtering options.
"""
import asyncio
import sys
import requests
from typing import Optional
from app.config import settings
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service

API_BASE_URL = "http://localhost:8000"
COLLECTION_NAME = "job_data"

def test_via_api(query: str, limit: int = 10, **filters):
    """Test job search via API endpoint."""
    try:
        print(f"🔍 Searching via API: '{query}'")
        if filters:
            print(f"   Filters: {filters}")
        
        payload = {
            "query": query,
            "limit": limit,
            **filters
        }
        
        response = requests.post(
            f"{API_BASE_URL}/jobs/{COLLECTION_NAME}/search",
            json=payload,
            timeout=60
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

async def test_via_service(query: str, limit: int = 10, **filters):
    """Test job search directly using services."""
    try:
        print(f"🔍 Searching via direct service: '{query}'")
        if filters:
            print(f"   Filters: {filters}")
        
        # Check if collection exists
        if not qdrant_service.collection_exists(COLLECTION_NAME):
            print(f"❌ Collection '{COLLECTION_NAME}' does not exist!")
            return None
        
        # Enhance query using LLM if enabled
        enhanced_query = query
        use_llm = filters.get('use_llm_enhancement', settings.ENABLE_LLM_QUERY_ENHANCEMENT)
        if use_llm and settings.OPENROUTER_API_KEY:
            enhanced_query = await llm_service.enhance_job_search_query(query)
            print(f"   Enhanced query: '{enhanced_query[:100]}...'")
        
        # Generate embedding
        query_vector = await embedding_service.generate_embedding(enhanced_query)
        
        # Build filter conditions
        filter_conditions = {}
        if filters.get('company_filter'):
            filter_conditions['company'] = filters['company_filter']
        
        # Search in Qdrant (request more if filtering needed)
        search_limit = limit
        if filters.get('certifications') or filters.get('min_experience_years'):
            search_limit = min(limit * 3, 100)
        
        results = qdrant_service.search_jobs(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=search_limit,
            score_threshold=filters.get('score_threshold'),
            filter_conditions=filter_conditions if filter_conditions else None
        )
        
        # Apply post-processing filters
        from app.api.jobs import filter_job_results
        filtered_results = filter_job_results(
            results=results,
            company_filter=None,  # Already filtered at Qdrant level
            min_experience_years=filters.get('min_experience_years'),
            certifications=filters.get('certifications'),
            limit=limit
        )
        
        return {
            "results": filtered_results,
            "count": len(filtered_results)
        }
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def display_results(data: dict, query: str, filters: dict = None):
    """Display search results in a formatted way."""
    if not data or data.get('count', 0) == 0:
        print(f"\n❌ No jobs found for query: '{query}'")
        if filters:
            print(f"   With filters: {filters}")
        return
    
    print(f"\n{'='*80}")
    print(f"✅ Found {data['count']} job(s) for query: '{query}'")
    if filters:
        print(f"   Filters applied: {filters}")
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
        
        # Show requirements snippet
        requirements = payload.get('job_requirements', '')
        if requirements:
            snippet = requirements[:200].replace('\n', ' ')
            print(f"\n✅ Requirements: {snippet}...")
        
        print()

async def run_tests():
    """Run comprehensive search tests."""
    print("="*80)
    print("Enhanced Job Search Test Suite")
    print("="*80)
    print()
    
    # Check collection
    try:
        if qdrant_service.collection_exists(COLLECTION_NAME):
            info = qdrant_service.get_collection_info(COLLECTION_NAME)
            print(f"✅ Collection '{COLLECTION_NAME}' exists")
            print(f"   Points in collection: {info.get('points_count', 0)}")
        else:
            print(f"❌ Collection '{COLLECTION_NAME}' does not exist")
            print(f"   Please import job data first using: python import_job_data.py")
            return 1
    except Exception as e:
        print(f"❌ Could not check collection: {str(e)}")
        return 1
    
    print()
    print("LLM Configuration:")
    print(f"   LLM Enhancement Enabled: {settings.ENABLE_LLM_QUERY_ENHANCEMENT}")
    print(f"   OpenRouter API Key: {'Set' if settings.OPENROUTER_API_KEY else 'Not set'}")
    print(f"   Model: {settings.OPENROUTER_MODEL}")
    print()
    
    # Test 1: Basic search
    print("\n" + "="*80)
    print("Test 1: Basic Search (with LLM enhancement)")
    print("="*80)
    result = test_via_api("software engineer", limit=5)
    if result is None:
        result = await test_via_service("software engineer", limit=5)
    if result:
        display_results(result, "software engineer")
    
    # Test 2: Search with company filter
    print("\n" + "="*80)
    print("Test 2: Search with Company Filter")
    print("="*80)
    result = test_via_api("developer", limit=5, company_filter="Jane Street")
    if result is None:
        result = await test_via_service("developer", limit=5, company_filter="Jane Street")
    if result:
        display_results(result, "developer", {"company_filter": "Jane Street"})
    
    # Test 3: Search with experience filter
    print("\n" + "="*80)
    print("Test 3: Search with Experience Filter (3+ years)")
    print("="*80)
    result = test_via_api("data analyst", limit=5, min_experience_years=3)
    if result is None:
        result = await test_via_service("data analyst", limit=5, min_experience_years=3)
    if result:
        display_results(result, "data analyst", {"min_experience_years": 3})
    
    # Test 4: Search with certifications filter
    print("\n" + "="*80)
    print("Test 4: Search with Certifications/Skills Filter")
    print("="*80)
    result = test_via_api("engineer", limit=5, certifications=["Python", "SQL"])
    if result is None:
        result = await test_via_service("engineer", limit=5, certifications=["Python", "SQL"])
    if result:
        display_results(result, "engineer", {"certifications": ["Python", "SQL"]})
    
    # Test 5: Combined filters
    print("\n" + "="*80)
    print("Test 5: Combined Filters (Company + Experience + Certifications)")
    print("="*80)
    result = test_via_api(
        "software engineer",
        limit=5,
        company_filter="Jane Street",
        min_experience_years=2,
        certifications=["Python"]
    )
    if result is None:
        result = await test_via_service(
            "software engineer",
            limit=5,
            company_filter="Jane Street",
            min_experience_years=2,
            certifications=["Python"]
        )
    if result:
        display_results(result, "software engineer", {
            "company_filter": "Jane Street",
            "min_experience_years": 2,
            "certifications": ["Python"]
        })
    
    # Test 6: Search without LLM enhancement
    print("\n" + "="*80)
    print("Test 6: Search without LLM Enhancement")
    print("="*80)
    result = test_via_api("Python developer", limit=5, use_llm_enhancement=False)
    if result is None:
        result = await test_via_service("Python developer", limit=5, use_llm_enhancement=False)
    if result:
        display_results(result, "Python developer", {"use_llm_enhancement": False})
    
    # Test 7: Search for financial/analyst roles
    print("\n" + "="*80)
    print("Test 7: Financial Analyst Search with Experience Filter")
    print("="*80)
    result = test_via_api("financial analyst", limit=5, min_experience_years=2)
    if result is None:
        result = await test_via_service("financial analyst", limit=5, min_experience_years=2)
    if result:
        display_results(result, "financial analyst", {"min_experience_years": 2})
    
    # Test 8: Search with multiple certifications
    print("\n" + "="*80)
    print("Test 8: Search with Multiple Certifications/Skills")
    print("="*80)
    result = test_via_api("manager", limit=5, certifications=["data", "Python", "SQL"])
    if result is None:
        result = await test_via_service("manager", limit=5, certifications=["data", "Python", "SQL"])
    if result:
        display_results(result, "manager", {"certifications": ["data", "Python", "SQL"]})
    
    # Test 9: High experience requirement filter
    print("\n" + "="*80)
    print("Test 9: High Experience Requirement (5+ years)")
    print("="*80)
    result = test_via_api("IT manager", limit=5, min_experience_years=5)
    if result is None:
        result = await test_via_service("IT manager", limit=5, min_experience_years=5)
    if result:
        display_results(result, "IT manager", {"min_experience_years": 5})
    
    # Test 10: Search with specific company and skills
    print("\n" + "="*80)
    print("Test 10: Company + Skills Filter (China Construction Bank)")
    print("="*80)
    result = test_via_api(
        "programmer",
        limit=5,
        company_filter="China Construction Bank",
        certifications=["SQL", "application"]
    )
    if result is None:
        result = await test_via_service(
            "programmer",
            limit=5,
            company_filter="China Construction Bank",
            certifications=["SQL", "application"]
        )
    if result:
        display_results(result, "programmer", {
            "company_filter": "China Construction Bank",
            "certifications": ["SQL", "application"]
        })
    
    # Test 11: Machine learning search with filters
    print("\n" + "="*80)
    print("Test 11: Machine Learning Search with Experience + Skills")
    print("="*80)
    result = test_via_api(
        "machine learning",
        limit=5,
        min_experience_years=3,
        certifications=["Python", "data"]
    )
    if result is None:
        result = await test_via_service(
            "machine learning",
            limit=5,
            min_experience_years=3,
            certifications=["Python", "data"]
        )
    if result:
        display_results(result, "machine learning", {
            "min_experience_years": 3,
            "certifications": ["Python", "data"]
        })
    
    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)
    return 0

async def main():
    """Main test function."""
    try:
        exit_code = await run_tests()
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

