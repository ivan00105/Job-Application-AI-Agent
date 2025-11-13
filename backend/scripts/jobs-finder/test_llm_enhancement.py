"""
Test script specifically for LLM query enhancement.
Tests how the LLM service enhances job search queries.
"""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import LLM service
services_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'jobs-finder')
sys.path.insert(0, services_path)
from llm_service import llm_service


async def test_query_enhancement(queries):
    """Test query enhancement for multiple queries"""
    print("=" * 70)
    print("LLM QUERY ENHANCEMENT TEST")
    print("=" * 70)
    print()
    
    # Check configuration
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("⚠️  WARNING: OPENROUTER_API_KEY not configured")
        print("   The LLM service will return original queries without enhancement")
        print("   Set OPENROUTER_API_KEY in your .env file to enable enhancement")
        print()
    
    print(f"OpenRouter Base URL: {os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')}")
    print(f"OpenRouter Model: {os.getenv('OPENROUTER_MODEL', 'openrouter/gpt-oss-120b')}")
    print()
    print("-" * 70)
    print()
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"Test {i}: Query Enhancement")
        print("-" * 70)
        print(f"Original Query: '{query}'")
        print()
        
        try:
            print("Enhancing query...")
            enhanced = await llm_service.enhance_job_search_query(query)
            
            if enhanced != query:
                print(f"✅ Query Enhanced!")
                print(f"Enhanced Query: '{enhanced}'")
                print()
                print("Improvements:")
                original_words = len(query.split())
                enhanced_words = len(enhanced.split())
                print(f"  - Word count: {original_words} → {enhanced_words} (+{enhanced_words - original_words})")
                print(f"  - Added relevant terms and synonyms")
            else:
                print(f"⚠️  Query not enhanced (returned original)")
                print("   This might mean:")
                print("   - OpenRouter API key not configured")
                print("   - API call failed")
                print("   - LLM returned empty/invalid response")
            
            results.append((query, enhanced, enhanced != query))
            
        except Exception as e:
            print(f"❌ Error enhancing query: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((query, query, False))
        
        print()
        print("-" * 70)
        print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    enhanced_count = sum(1 for _, _, enhanced in results if enhanced)
    total = len(results)
    
    for i, (original, enhanced, was_enhanced) in enumerate(results, 1):
        status = "✅ ENHANCED" if was_enhanced else "⚠️  NOT ENHANCED"
        print(f"{i}. {status}: '{original}'")
        if was_enhanced:
            print(f"   → '{enhanced}'")
    
    print()
    print(f"Total: {enhanced_count}/{total} queries enhanced")
    print("=" * 70)
    print()
    
    return enhanced_count > 0


async def test_enhancement_examples():
    """Test with various example queries"""
    test_queries = [
        "Python developer",
        "data scientist",
        "machine learning engineer",
        "cloud architect",
        "frontend developer",
        "project manager",
        "cybersecurity analyst",
        "devops engineer"
    ]
    
    return await test_query_enhancement(test_queries)


async def test_custom_query():
    """Test with a custom query from command line"""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        await test_query_enhancement([query])
    else:
        print("Usage: python test_llm_enhancement.py 'your search query'")
        print("Or run with examples: python test_llm_enhancement.py")


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        # Test custom query
        await test_custom_query()
    else:
        # Test example queries
        await test_enhancement_examples()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

