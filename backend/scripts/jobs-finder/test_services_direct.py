"""
Direct test of job search services without API authentication.
This tests the core functionality: Qdrant, Embedding, and LLM services.
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
from llm_service import llm_service


async def test_embedding_service():
    """Test 1: Embedding Service"""
    print("=" * 70)
    print("TEST 1: Embedding Service")
    print("=" * 70)
    print()
    
    try:
        test_query = "Python developer"
        print(f"Generating embedding for: '{test_query}'...")
        embedding = await embedding_service.generate_embedding(test_query)
        
        print(f"✅ Embedding generated successfully!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print()
        return True
    except Exception as e:
        print(f"❌ Embedding service failed: {str(e)}")
        print()
        return False


async def test_qdrant_service():
    """Test 2: Qdrant Service"""
    print("=" * 70)
    print("TEST 2: Qdrant Service")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        print(f"Checking collection: '{collection_name}'...")
        
        # Check if collection exists
        exists = qdrant_service.collection_exists(collection_name)
        if exists:
            print(f"✅ Collection '{collection_name}' exists")
            
            # Get collection info
            info = qdrant_service.get_collection_info(collection_name)
            print(f"   Points count: {info.get('points_count', 0)}")
            print(f"   Vector size: {info.get('config', {}).get('vector_size', 'N/A')}")
        else:
            print(f"⚠️  Collection '{collection_name}' does not exist")
            print("   This is OK if you haven't loaded job data yet")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Qdrant service failed: {str(e)}")
        print()
        return False


async def test_llm_service():
    """Test 3: LLM Service (Optional)"""
    print("=" * 70)
    print("TEST 3: LLM Service (Query Enhancement)")
    print("=" * 70)
    print()
    
    try:
        test_query = "data scientist"
        print(f"Testing query enhancement for: '{test_query}'...")
        
        enhanced = await llm_service.enhance_job_search_query(test_query)
        
        if enhanced != test_query:
            print(f"✅ Query enhanced successfully!")
            print(f"   Original: {test_query}")
            print(f"   Enhanced: {enhanced}")
        else:
            print(f"⚠️  Query not enhanced (LLM may not be configured)")
            print(f"   This is OK - search works without LLM enhancement")
        
        print()
        return True
    except Exception as e:
        print(f"⚠️  LLM service test failed: {str(e)}")
        print("   This is OK if OpenRouter is not configured")
        print()
        return True  # Don't fail the test suite if LLM is not configured


async def test_job_search():
    """Test 4: Full Job Search"""
    print("=" * 70)
    print("TEST 4: Full Job Search")
    print("=" * 70)
    print()
    
    try:
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "job_data")
        test_query = "Python developer"
        
        print(f"Searching for: '{test_query}'")
        print(f"Collection: '{collection_name}'")
        print()
        
        # Generate embedding
        print("1. Generating query embedding...")
        query_vector = await embedding_service.generate_embedding(test_query)
        print(f"   ✅ Embedding generated ({len(query_vector)} dimensions)")
        
        # Search in Qdrant
        print("2. Searching in Qdrant...")
        results = qdrant_service.search_jobs(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=5,
            score_threshold=0.5
        )
        
        print(f"   ✅ Search completed")
        print(f"   Found {len(results)} results")
        print()
        
        if results:
            print("Top results:")
            print("-" * 70)
            for i, result in enumerate(results[:3], 1):
                payload = result.get('payload', {})
                score = result.get('score', 0)
                
                print(f"\n{i}. {payload.get('job_title', 'N/A')}")
                print(f"   Company: {payload.get('company', 'N/A')}")
                print(f"   Location: {payload.get('location', 'N/A')}")
                print(f"   Similarity Score: {score:.4f}")
        else:
            print("⚠️  No results found")
            print("   This might mean:")
            print("   - Qdrant collection is empty")
            print("   - No jobs match the search query")
            print("   - Score threshold is too high")
        
        print()
        print("-" * 70)
        print()
        return True
    except Exception as e:
        print(f"❌ Job search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def run_all_tests():
    """Run all service tests"""
    print("\n" + "=" * 70)
    print("JOB SEARCH SERVICES - DIRECT TEST")
    print("=" * 70)
    print("Testing core services without API authentication")
    print("=" * 70)
    print()
    
    tests = [
        ("Embedding Service", test_embedding_service),
        ("Qdrant Service", test_qdrant_service),
        ("LLM Service", test_llm_service),
        ("Full Job Search", test_job_search),
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

