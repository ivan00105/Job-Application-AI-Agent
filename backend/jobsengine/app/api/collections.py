from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import (
    CollectionCreate, CollectionRename, CollectionInfo, SuccessResponse
)
from app.services.qdrant_service import qdrant_service

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.post("/", response_model=SuccessResponse)
async def create_collection(collection: CollectionCreate):
    """Create a new collection."""
    try:
        qdrant_service.create_collection(collection.name)
        return SuccessResponse(
            success=True,
            message=f"Collection '{collection.name}' created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")

@router.get("/", response_model=List[str])
async def list_collections():
    """List all collections."""
    try:
        return qdrant_service.list_collections()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing collections: {str(e)}")

@router.get("/{collection_name}", response_model=CollectionInfo)
async def get_collection_info(collection_name: str):
    """Get collection information."""
    try:
        info = qdrant_service.get_collection_info(collection_name)
        return CollectionInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")

@router.put("/rename", response_model=SuccessResponse)
async def rename_collection(rename: CollectionRename):
    """Rename a collection."""
    try:
        qdrant_service.rename_collection(rename.old_name, rename.new_name)
        return SuccessResponse(
            success=True,
            message=f"Collection '{rename.old_name}' renamed to '{rename.new_name}'"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming collection: {str(e)}")

@router.delete("/{collection_name}", response_model=SuccessResponse)
async def delete_collection(collection_name: str):
    """Delete a collection."""
    try:
        qdrant_service.delete_collection(collection_name)
        return SuccessResponse(
            success=True,
            message=f"Collection '{collection_name}' deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting collection: {str(e)}")

