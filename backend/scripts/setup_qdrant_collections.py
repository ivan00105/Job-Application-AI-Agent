"""Setup script to create required Qdrant collections via JobsEngine API"""
import asyncio
import httpx
from config import get_settings

settings = get_settings()


async def create_collection(collection_name: str):
    """Create a single collection"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.jobsengine_url}/collections/",
                json={"name": collection_name}
            )
            response.raise_for_status()
            print(f"Created collection: {collection_name}")
            return True
        except httpx.HTTPStatusError as e:
            if "already exists" in str(e.response.text).lower():
                print(f"Collection already exists: {collection_name}")
                return True
            else:
                print(f"Error creating {collection_name}: {e.response.text}")
                return False
        except Exception as e:
            print(f"Error creating {collection_name}: {str(e)}")
            return False


async def list_collections():
    """List all existing collections"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{settings.jobsengine_url}/collections/")
            response.raise_for_status()
            collections = response.json()
            print(f"\nExisting collections: {collections}")
            return collections
        except Exception as e:
            print(f"Error listing collections: {str(e)}")
            return []


async def main():
    """Main setup function"""
    print("Setting up Qdrant collections for Job Application Agent\n")
    print(f"JobsEngine URL: {settings.jobsengine_url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.jobsengine_url}/collections/")
            response.raise_for_status()
            print("Successfully connected to JobsEngine\n")
    except Exception as e:
        print(f"Cannot connect to JobsEngine at {settings.jobsengine_url}")
        print(f"Error: {str(e)}")
        print("\nMake sure JobsEngine is running and the URL in .env is correct.")
        return
    
    collections = [
        "job_embeddings",
        "cv_embeddings",
        "agent_memory_embeddings"
    ]
    
    print("Creating collections...\n")
    
    success_count = 0
    for collection in collections:
        if await create_collection(collection):
            success_count += 1
    
    print(f"\nSetup complete: {success_count}/{len(collections)} collections ready")
    await list_collections()
    
    print("\nNext steps:")
    print("  1. Run database migration: python scripts/run_migration.py")
    print("  2. Create test users: python scripts/create_test_users.py")
    print("  3. Start the backend: python main.py")


if __name__ == "__main__":
    asyncio.run(main())

