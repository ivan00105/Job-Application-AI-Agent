"""
Demo script showing how LLM query enhancement works.
This script demonstrates the enhancement logic and shows examples
of what enhanced queries would look like.
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


def show_enhancement_examples():
    """Show examples of what query enhancement does"""
    print("=" * 70)
    print("LLM QUERY ENHANCEMENT - HOW IT WORKS")
    print("=" * 70)
    print()
    print("Query enhancement expands your search query with:")
    print("  - Relevant synonyms and related terms")
    print("  - Common variations of job titles")
    print("  - Technical terms, tools, and methodologies")
    print("  - Related skills and certifications")
    print()
    print("Example Enhancements:")
    print("-" * 70)
    print()
    
    examples = [
        ("Python developer", 
         "Python developer software engineer programming Python Django Flask FastAPI backend development"),
        ("data scientist",
         "data scientist data analyst business analyst data analytics SQL Python R Tableau Power BI machine learning"),
        ("machine learning engineer",
         "machine learning ML engineer data scientist AI artificial intelligence deep learning neural networks TensorFlow PyTorch"),
        ("cloud architect",
         "cloud architect AWS Azure GCP cloud infrastructure DevOps Kubernetes Docker microservices architecture"),
        ("frontend developer",
         "frontend developer front-end engineer web developer React Vue Angular JavaScript TypeScript HTML CSS UI UX"),
    ]
    
    for original, enhanced in examples:
        print(f"Original:  '{original}'")
        print(f"Enhanced:  '{enhanced}'")
        print(f"Words:     {len(original.split())} → {len(enhanced.split())} (+{len(enhanced.split()) - len(original.split())})")
        print()


async def test_actual_enhancement():
    """Test actual LLM enhancement if API key is configured"""
    print("=" * 70)
    print("TESTING ACTUAL LLM ENHANCEMENT")
    print("=" * 70)
    print()
    
    # Check configuration
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        print("❌ OpenRouter API Key not configured")
        print()
        print("To enable LLM query enhancement:")
        print("1. Get an API key from https://openrouter.ai/")
        print("2. Add to your .env file:")
        print("   OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("3. Optional settings:")
        print("   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1")
        print("   OPENROUTER_MODEL=openrouter/gpt-oss-120b")
        print("   OPENROUTER_TEMPERATURE=0.7")
        print("   OPENROUTER_MAX_TOKENS=200")
        print()
        return False
    
    print(f"✅ OpenRouter API Key configured (length: {len(api_key)})")
    print(f"   Model: {os.getenv('OPENROUTER_MODEL', 'openrouter/gpt-oss-120b')}")
    print()
    print("-" * 70)
    print()
    
    test_queries = [
        "Python developer",
        "data scientist",
        "machine learning engineer"
    ]
    
    for query in test_queries:
        print(f"Testing: '{query}'")
        print("-" * 70)
        
        try:
            enhanced = await llm_service.enhance_job_search_query(query)
            
            if enhanced != query:
                print(f"✅ Enhanced successfully!")
                print(f"Original:  '{query}'")
                print(f"Enhanced:  '{enhanced}'")
                print(f"Words:     {len(query.split())} → {len(enhanced.split())}")
            else:
                print(f"⚠️  Query not enhanced (returned original)")
                print("   Check API key and network connection")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
    
    return True


async def main():
    """Main function"""
    # Show examples first
    show_enhancement_examples()
    
    # Test actual enhancement
    print()
    print("=" * 70)
    print()
    await test_actual_enhancement()
    
    print("=" * 70)
    print("Note: Query enhancement is OPTIONAL")
    print("Job search works perfectly fine without it!")
    print("Enhancement just improves search results by expanding queries.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

