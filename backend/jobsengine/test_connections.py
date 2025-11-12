"""
Test script to verify Qdrant and Ollama server connections.
Run this script to check if both services are properly configured and accessible.
"""
import asyncio
import sys
from app.config import settings
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
import httpx

def test_qdrant_connection():
    """Test Qdrant server connection."""
    print("=" * 60)
    print("Testing Qdrant Connection")
    print("=" * 60)
    
    try:
        # Try to get collections (this will fail if connection is bad)
        collections = qdrant_service.list_collections()
        print(f"✅ Qdrant connection successful!")
        print(f"   Host: {settings.QDRANT_HOST}")
        print(f"   Port: {settings.QDRANT_PORT}")
        if settings.QDRANT_PATH:
            print(f"   Path: {settings.QDRANT_PATH} (local mode)")
        print(f"   Existing collections: {collections if collections else 'None'}")
        return True
    except Exception as e:
        print(f"❌ Qdrant connection failed!")
        print(f"   Error: {str(e)}")
        print(f"   Host: {settings.QDRANT_HOST}")
        print(f"   Port: {settings.QDRANT_PORT}")
        if settings.QDRANT_PATH:
            print(f"   Path: {settings.QDRANT_PATH}")
        print("\n   Troubleshooting:")
        print("   - Make sure Qdrant server is running")
        print("   - Check QDRANT_HOST and QDRANT_PORT in .env file")
        print("   - For local mode, ensure QDRANT_PATH is set correctly")
        return False

async def test_ollama_connection():
    """Test Ollama server connection and model availability."""
    print("\n" + "=" * 60)
    print("Testing Ollama Connection")
    print("=" * 60)
    
    try:
        # Test if Ollama server is reachable
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if server is up
            try:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                response.raise_for_status()
                print(f"✅ Ollama server is reachable!")
                print(f"   URL: {settings.OLLAMA_BASE_URL}")
                
                # Check if model is available
                models_data = response.json()
                available_models = [model.get("name", "") for model in models_data.get("models", [])]
                model_found = any(settings.OLLAMA_EMBEDDING_MODEL in model for model in available_models)
                
                if model_found:
                    print(f"✅ Model '{settings.OLLAMA_EMBEDDING_MODEL}' is available!")
                else:
                    print(f"⚠️  Model '{settings.OLLAMA_EMBEDDING_MODEL}' not found in available models")
                    print(f"   Available models: {', '.join(available_models) if available_models else 'None'}")
                    print(f"   Run: ollama pull {settings.OLLAMA_EMBEDDING_MODEL}")
                
                return True
            except httpx.ConnectError:
                print(f"❌ Cannot connect to Ollama server!")
                print(f"   URL: {settings.OLLAMA_BASE_URL}")
                print("\n   Troubleshooting:")
                print("   - Make sure Ollama server is running")
                print("   - Check OLLAMA_BASE_URL in .env file")
                print("   - Try: ollama serve")
                return False
    except Exception as e:
        print(f"❌ Ollama connection test failed!")
        print(f"   Error: {str(e)}")
        return False

async def test_embedding_generation():
    """Test embedding generation with Ollama."""
    print("\n" + "=" * 60)
    print("Testing Embedding Generation")
    print("=" * 60)
    
    try:
        test_text = "This is a test sentence for embedding generation."
        print(f"   Generating embedding for: '{test_text[:50]}...'")
        
        embedding = await embedding_service.generate_embedding(test_text)
        
        print(f"✅ Embedding generated successfully!")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   Expected dimension: {settings.EMBEDDING_DIM}")
        
        if len(embedding) == settings.EMBEDDING_DIM:
            print(f"✅ Embedding dimension matches configuration!")
        else:
            print(f"⚠️  Warning: Embedding dimension ({len(embedding)}) doesn't match")
            print(f"   expected dimension ({settings.EMBEDDING_DIM})")
            print(f"   Update EMBEDDING_DIM in .env file")
        
        # Show first few values
        print(f"   First 5 values: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"❌ Embedding generation failed!")
        print(f"   Error: {str(e)}")
        print("\n   Troubleshooting:")
        print(f"   - Make sure model '{settings.OLLAMA_EMBEDDING_MODEL}' is pulled")
        print(f"   - Run: ollama pull {settings.OLLAMA_EMBEDDING_MODEL}")
        return False

async def test_full_workflow():
    """Test a complete workflow: create collection, save data, search."""
    print("\n" + "=" * 60)
    print("Testing Full Workflow")
    print("=" * 60)
    
    test_collection = "test_jobs_connection_check"
    
    try:
        # Clean up if test collection exists
        if qdrant_service.collection_exists(test_collection):
            print(f"   Cleaning up existing test collection...")
            qdrant_service.delete_collection(test_collection)
        
        # Create collection
        print(f"   1. Creating test collection '{test_collection}'...")
        qdrant_service.create_collection(test_collection)
        print(f"   ✅ Collection created")
        
        # Generate embedding and save test data
        print(f"   2. Generating embedding and saving test data...")
        test_text = "Python developer with machine learning experience"
        embedding = await embedding_service.generate_embedding(test_text)
        
        qdrant_service.save_job_data(
            collection_name=test_collection,
            job_id=999,
            vector=embedding,
            payload={
                "title": "Test Job",
                "description": test_text,
                "company": "Test Corp"
            }
        )
        print(f"   ✅ Test data saved")
        
        # Search
        print(f"   3. Testing search functionality...")
        search_query = "machine learning Python"
        query_embedding = await embedding_service.generate_embedding(search_query)
        
        results = qdrant_service.search_jobs(
            collection_name=test_collection,
            query_vector=query_embedding,
            limit=5
        )
        
        print(f"   ✅ Search completed")
        print(f"   Found {len(results)} result(s)")
        if results:
            print(f"   Top result score: {results[0]['score']:.4f}")
        
        # Clean up
        print(f"   4. Cleaning up test collection...")
        qdrant_service.delete_collection(test_collection)
        print(f"   ✅ Test collection deleted")
        
        print(f"\n✅ Full workflow test passed!")
        return True
    except Exception as e:
        print(f"❌ Full workflow test failed!")
        print(f"   Error: {str(e)}")
        
        # Try to clean up on error
        try:
            if qdrant_service.collection_exists(test_collection):
                qdrant_service.delete_collection(test_collection)
                print(f"   (Test collection cleaned up)")
        except:
            pass
        
        return False

def print_configuration():
    """Print current configuration."""
    print("=" * 60)
    print("Current Configuration")
    print("=" * 60)
    print(f"Qdrant:")
    print(f"  Host: {settings.QDRANT_HOST}")
    print(f"  Port: {settings.QDRANT_PORT}")
    if settings.QDRANT_PATH:
        print(f"  Path: {settings.QDRANT_PATH} (local mode)")
    print(f"\nOllama:")
    print(f"  Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"  Model: {settings.OLLAMA_EMBEDDING_MODEL}")
    print(f"\nEmbedding:")
    print(f"  Dimension: {settings.EMBEDDING_DIM}")
    print()

async def main():
    """Run all connection tests."""
    print("\n" + "=" * 60)
    print("Connection Test Suite")
    print("=" * 60)
    print()
    
    print_configuration()
    
    # Test Qdrant
    qdrant_ok = test_qdrant_connection()
    
    # Test Ollama
    ollama_ok = await test_ollama_connection()
    
    # Test embedding generation
    embedding_ok = False
    if ollama_ok:
        embedding_ok = await test_embedding_generation()
    
    # Test full workflow if both services are working
    workflow_ok = False
    if qdrant_ok and embedding_ok:
        workflow_ok = await test_full_workflow()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Qdrant Connection:        {'✅ PASS' if qdrant_ok else '❌ FAIL'}")
    print(f"Ollama Connection:        {'✅ PASS' if ollama_ok else '❌ FAIL'}")
    print(f"Embedding Generation:     {'✅ PASS' if embedding_ok else '❌ FAIL'}")
    print(f"Full Workflow:            {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    print()
    
    if all([qdrant_ok, ollama_ok, embedding_ok, workflow_ok]):
        print("🎉 All tests passed! Your setup is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

