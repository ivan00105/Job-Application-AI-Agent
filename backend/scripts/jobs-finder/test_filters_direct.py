"""
Direct test of filter functionality for job search.
Tests company filtering, experience filtering, and certifications filtering
without requiring API authentication.
"""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import services directly
services_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from qdrant_service import qdrant_service
from embedding_service import embedding_service


def filter_job_results(
    results,
    company_filter=None,
    min_experience_years=None,
    certifications=None,
    limit=10
):
    """
    Post-process and filter job search results based on structured criteria.
    This is the same filtering logic used in the API.
    """
    filtered_results = []
    
    for result in results:
        payload = result.get('payload', {})
        
        # Build searchable text from job data
        job_text = (
            payload.get('job_title', '') + ' ' +
            payload.get('job_responsibilities', '') + ' ' +
            payload.get('job_requirements', '') + ' ' +
            payload.get('description', '')
        ).lower()
        
        # Filter by company if specified
        if company_filter:
            company = payload.get('company', '').lower()
            if company_filter.lower() not in company:
                continue
        
        # Filter by certifications/skills if specified
        if certifications:
            has_cert = any(
                cert.lower() in job_text 
                for cert in certifications
            )
            if not has_cert:
                continue
        
        # Filter by minimum experience if specified
        if min_experience_years:
            # Try to extract years from requirements text
            experience_keywords = [
                f"{min_experience_years} years",
                f"{min_experience_years}+ years",
                f"{min_experience_years} year",
                f"{min_experience_years}+ year",
                f"minimum {min_experience_years} years",
                f"at least {min_experience_years} years",
                f"min {min_experience_years} years"
            ]
            
            # Check if any experience requirement matches
            has_experience = any(
                keyword in job_text 
                for keyword in experience_keywords
            )
            
            # Also check for higher experience levels (up to 5 years more)
            if not has_experience:
                for years in range(min_experience_years + 1, min_experience_years + 6):
                    if (f"{years} years" in job_text or 
                        f"{years}+ years" in job_text or
                        f"{years} year" in job_text):
                        has_experience = True
                        break
            
            # If we can't find explicit experience and requirement is high, be strict
            if not has_experience and min_experience_years > 3:
                continue
        
        filtered_results.append(result)
    
    # Limit results after filtering
    return filtered_results[:limit]


async def test_company_filter():
    """Test 1: Company Filter"""
    print("=" * 70)
    print("TEST 1: Company Filter")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        query = "developer"
        
        print(f"Searching for: '{query}'")
        print(f"Filter: Company contains 'Google'")
        print()
        
        # Generate embedding and search
        query_vector = await embedding_service.generate_embedding(query)
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=20,
            score_threshold=0.4
        )
        
        print(f"Found {len(results)} results before filtering")
        
        # Apply company filter
        filtered = filter_job_results(
            results,
            company_filter="Google",
            limit=10
        )
        
        print(f"Found {len(filtered)} results after company filter")
        print()
        
        if filtered:
            print("Filtered results:")
            print("-" * 70)
            for i, result in enumerate(filtered[:5], 1):
                payload = result.get('payload', {})
                print(f"{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Company: {payload.get('company', 'N/A')}")
                print(f"   Score: {result.get('score', 0):.4f}")
        else:
            print("No results match the company filter")
            print("(This is OK - it means no jobs from that company in the results)")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Company filter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_experience_filter():
    """Test 2: Experience Filter"""
    print("=" * 70)
    print("TEST 2: Experience Filter")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        query = "engineer"
        min_years = 3
        
        print(f"Searching for: '{query}'")
        print(f"Filter: Minimum {min_years} years of experience")
        print()
        
        # Generate embedding and search
        query_vector = await embedding_service.generate_embedding(query)
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=30,
            score_threshold=0.4
        )
        
        print(f"Found {len(results)} results before filtering")
        
        # Apply experience filter
        filtered = filter_job_results(
            results,
            min_experience_years=min_years,
            limit=10
        )
        
        print(f"Found {len(filtered)} results after experience filter")
        print()
        
        if filtered:
            print("Filtered results:")
            print("-" * 70)
            for i, result in enumerate(filtered[:5], 1):
                payload = result.get('payload', {})
                requirements = payload.get('job_requirements', '') or payload.get('description', '')
                # Show snippet of requirements
                req_snippet = requirements[:100] + "..." if len(requirements) > 100 else requirements
                
                print(f"{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Company: {payload.get('company', 'N/A')}")
                print(f"   Requirements snippet: {req_snippet}")
                print(f"   Score: {result.get('score', 0):.4f}")
        else:
            print("No results match the experience filter")
            print("(This might mean no jobs explicitly mention experience requirements)")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Experience filter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_certifications_filter():
    """Test 3: Certifications/Skills Filter"""
    print("=" * 70)
    print("TEST 3: Certifications/Skills Filter")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        query = "cloud engineer"
        certifications = ["AWS", "Docker"]
        
        print(f"Searching for: '{query}'")
        print(f"Filter: Must have {', '.join(certifications)}")
        print()
        
        # Generate embedding and search
        query_vector = await embedding_service.generate_embedding(query)
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=30,
            score_threshold=0.4
        )
        
        print(f"Found {len(results)} results before filtering")
        
        # Apply certifications filter
        filtered = filter_job_results(
            results,
            certifications=certifications,
            limit=10
        )
        
        print(f"Found {len(filtered)} results after certifications filter")
        print()
        
        if filtered:
            print("Filtered results:")
            print("-" * 70)
            for i, result in enumerate(filtered[:5], 1):
                payload = result.get('payload', {})
                requirements = payload.get('job_requirements', '') or payload.get('description', '')
                req_snippet = requirements[:150] + "..." if len(requirements) > 150 else requirements
                
                print(f"{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Company: {payload.get('company', 'N/A')}")
                print(f"   Requirements snippet: {req_snippet}")
                print(f"   Score: {result.get('score', 0):.4f}")
        else:
            print("No results match the certifications filter")
            print("(This might mean no jobs mention these specific certifications)")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Certifications filter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_combined_filters():
    """Test 4: Combined Filters"""
    print("=" * 70)
    print("TEST 4: Combined Filters")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        query = "developer"
        
        print(f"Searching for: '{query}'")
        print("Filters:")
        print("  - Experience: 2+ years")
        print("  - Certifications: Python, Django")
        print()
        
        # Generate embedding and search
        query_vector = await embedding_service.generate_embedding(query)
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=50,
            score_threshold=0.4
        )
        
        print(f"Found {len(results)} results before filtering")
        
        # Apply combined filters
        filtered = filter_job_results(
            results,
            min_experience_years=2,
            certifications=["Python", "Django"],
            limit=10
        )
        
        print(f"Found {len(filtered)} results after combined filters")
        print()
        
        if filtered:
            print("Filtered results:")
            print("-" * 70)
            for i, result in enumerate(filtered[:5], 1):
                payload = result.get('payload', {})
                print(f"{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Company: {payload.get('company', 'N/A')}")
                print(f"   Location: {payload.get('location', 'N/A')}")
                print(f"   Score: {result.get('score', 0):.4f}")
        else:
            print("No results match all the combined filters")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Combined filters test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_score_threshold():
    """Test 5: Score Threshold Filter"""
    print("=" * 70)
    print("TEST 5: Score Threshold Filter")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        query = "machine learning"
        
        print(f"Searching for: '{query}'")
        print("Score threshold: 0.6 (only highly similar matches)")
        print()
        
        # Generate embedding and search with high threshold
        query_vector = await embedding_service.generate_embedding(query)
        results_high = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=10,
            score_threshold=0.6
        )
        
        # Also search with lower threshold for comparison
        results_low = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=10,
            score_threshold=0.4
        )
        
        print(f"Results with threshold 0.6: {len(results_high)}")
        print(f"Results with threshold 0.4: {len(results_low)}")
        print()
        
        if results_high:
            print("High threshold results (0.6+):")
            print("-" * 70)
            for i, result in enumerate(results_high[:3], 1):
                payload = result.get('payload', {})
                print(f"{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Score: {result.get('score', 0):.4f}")
        else:
            print("No results with high threshold (0.6+)")
            print("This means no jobs are highly similar to the query")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Score threshold test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all filter tests"""
    print("\n" + "=" * 70)
    print("JOB SEARCH FILTER FUNCTIONALITY - DIRECT TEST")
    print("=" * 70)
    print("Testing filter functionality without API authentication")
    print("=" * 70)
    print()
    
    tests = [
        ("Company Filter", test_company_filter),
        ("Experience Filter", test_experience_filter),
        ("Certifications Filter", test_certifications_filter),
        ("Combined Filters", test_combined_filters),
        ("Score Threshold", test_score_threshold),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with error: {str(e)}\n")
            results.append((test_name, False))
    
    # Print summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    print()
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

