"""
Script to import job data from CSV file into Qdrant vector database.
Creates a collection and imports all job records with embeddings.
"""
import csv
import asyncio
import sys
from typing import List, Dict, Any
from app.config import settings
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service

# Collection name - can be customized
COLLECTION_NAME = "job_data"

def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Read job data from CSV file with multiline field support."""
    jobs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            # csv.DictReader should handle multiline quoted fields automatically
            reader = csv.DictReader(f)
            
            for idx, row in enumerate(reader, start=1):
                # Extract data with proper field names (handle BOM in first column)
                company = row.get('Company', row.get('\ufeffCompany', '')).strip()
                title = row.get('Job Title', '').strip()
                responsibilities = row.get('Job Responsibilities', '').strip()
                requirements = row.get('Job Requirements', '').strip()
                to_apply = row.get('To Apply', '').strip()
                job_date = row.get('JobDate', '').strip()
                
                # Skip empty rows
                if not company or not title:
                    continue
                
                # Combine text fields for embedding
                job_text_parts = []
                if title:
                    job_text_parts.append(f"Job Title: {title}")
                if responsibilities:
                    job_text_parts.append(f"Responsibilities: {responsibilities}")
                if requirements:
                    job_text_parts.append(f"Requirements: {requirements}")
                
                job_text = "\n".join(job_text_parts)
                
                # Create job record
                job = {
                    'id': idx,
                    'text': job_text,
                    'payload': {
                        'company': company,
                        'job_title': title,
                        'job_responsibilities': responsibilities,
                        'job_requirements': requirements,
                        'to_apply': to_apply,
                        'job_date': job_date
                    }
                }
                jobs.append(job)
        
        return jobs
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def create_collection_if_not_exists(collection_name: str):
    """Create collection if it doesn't exist."""
    try:
        if qdrant_service.collection_exists(collection_name):
            print(f"⚠️  Collection '{collection_name}' already exists.")
            response = input("Do you want to delete it and create a new one? (yes/no): ").strip().lower()
            if response == 'yes':
                print(f"   Deleting existing collection...")
                qdrant_service.delete_collection(collection_name)
                print(f"   Creating new collection...")
                qdrant_service.create_collection(collection_name)
                print(f"✅ Collection '{collection_name}' created successfully!")
            else:
                print(f"   Keeping existing collection. New data will be added/updated.")
        else:
            print(f"   Creating collection '{collection_name}'...")
            qdrant_service.create_collection(collection_name)
            print(f"✅ Collection '{collection_name}' created successfully!")
    except Exception as e:
        print(f"❌ Error creating collection: {str(e)}")
        sys.exit(1)

async def import_jobs(jobs: List[Dict[str, Any]], collection_name: str, batch_size: int = 10):
    """Import jobs into Qdrant with progress tracking."""
    total = len(jobs)
    print(f"\n📊 Importing {total} jobs into collection '{collection_name}'...")
    print(f"   Batch size: {batch_size}")
    print(f"   This may take a while depending on the number of jobs...\n")
    
    imported = 0
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = jobs[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} jobs)...")
        
        try:
            # Generate embeddings for batch
            texts = [job['text'] for job in batch]
            embeddings = await embedding_service.generate_embeddings_batch(texts)
            
            # Save to Qdrant
            for job, embedding in zip(batch, embeddings):
                try:
                    qdrant_service.save_job_data(
                        collection_name=collection_name,
                        job_id=job['id'],
                        vector=embedding,
                        payload=job['payload']
                    )
                    imported += 1
                except Exception as e:
                    print(f"      ⚠️  Failed to save job ID {job['id']}: {str(e)}")
                    failed += 1
            
            # Progress update
            progress = (imported / total) * 100
            print(f"      ✅ Progress: {imported}/{total} ({progress:.1f}%)")
            
        except Exception as e:
            print(f"      ❌ Error processing batch {batch_num}: {str(e)}")
            failed += len(batch)
    
    print(f"\n{'='*60}")
    print(f"Import Summary")
    print(f"{'='*60}")
    print(f"✅ Successfully imported: {imported} jobs")
    if failed > 0:
        print(f"❌ Failed: {failed} jobs")
    print(f"📊 Total processed: {total} jobs")
    print(f"\n✅ Import completed!")

async def main():
    """Main function to import job data."""
    print("=" * 60)
    print("Job Data Import Script")
    print("=" * 60)
    print()
    
    # Configuration
    csv_file = "test_job_data.csv"
    collection_name = COLLECTION_NAME
    
    print(f"Configuration:")
    print(f"  CSV File: {csv_file}")
    print(f"  Collection: {collection_name}")
    print(f"  Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    if settings.QDRANT_PATH:
        print(f"  Qdrant Path: {settings.QDRANT_PATH} (local mode)")
    print(f"  Ollama: {settings.OLLAMA_BASE_URL}")
    print(f"  Model: {settings.OLLAMA_EMBEDDING_MODEL}")
    print()
    
    # Read CSV
    print(f"📖 Reading CSV file '{csv_file}'...")
    jobs = read_csv_file(csv_file)
    print(f"✅ Found {len(jobs)} jobs in CSV file")
    
    if len(jobs) == 0:
        print("❌ No jobs found in CSV file. Exiting.")
        sys.exit(1)
    
    # Create collection
    await create_collection_if_not_exists(collection_name)
    
    # Import jobs
    await import_jobs(jobs, collection_name, batch_size=10)
    
    # Show collection info
    print(f"\n📊 Collection Information:")
    try:
        info = qdrant_service.get_collection_info(collection_name)
        print(f"   Name: {info['name']}")
        print(f"   Points: {info['points_count']}")
        print(f"   Vectors: {info['vectors_count']}")
        print(f"   Vector Size: {info['config']['vector_size']}")
        print(f"   Distance: {info['config']['distance']}")
    except Exception as e:
        print(f"   ⚠️  Could not retrieve collection info: {str(e)}")
    
    print(f"\n🎉 All done! You can now search the job data using the API.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

