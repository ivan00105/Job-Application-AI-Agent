"""
Simple non-interactive test script to search for jobs.
This script automatically tests job search without user interaction.
"""
import asyncio
import sys
from app.config import settings
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service

COLLECTION_NAME = "job_data"

async def search_jobs(query: str, limit: int = 5):
    """Search for jobs using the direct service."""
    try:
        print(f"🔍 Searching for: '{query}'...")
        
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
        
        return results
    except Exception as e:
        print(f"❌ Search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def display_results(results: list, query: str):
    """Display search results."""
    if not results or len(results) == 0:
        print(f"❌ No jobs found for query: '{query}'\n")
        return
    
    print(f"\n{'='*80}")
    print(f"✅ Found {len(results)} job(s) for query: '{query}'")
    print(f"{'='*80}\n")
    
    for i, result in enumerate(results, 1):
        payload = result.get('payload', {})
        score = result.get('score', 0)
        
        print(f"{i}. {payload.get('job_title', 'N/A')} at {payload.get('company', 'N/A')}")
        print(f"   Similarity Score: {score:.4f}")
        print(f"   Date: {payload.get('job_date', 'N/A')}")
        print()

async def main():
    """Main test function."""
    print("="*80)
    print("Job Search Test - Simple Version")
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
    
    # Test queries
    test_queries = [
        "software engineer",
        "data analyst",
        "Python developer",
        "machine learning engineer"
    ]
    
    print("Testing job search with multiple queries:\n")
    
    for query in test_queries:
        results = await search_jobs(query, limit=3)
        if results:
            display_results(results, query)
        else:
            print(f"❌ Failed to search for '{query}'\n")
    
    print("="*80)
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


