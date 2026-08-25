from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/v1", tags=["Memories"])


class MemoryCreateRequest(BaseModel):
    content: str = Field(..., description="The memory text to store")
    user_id: str = Field("default", description="User ID or 'default'")
    project: str = Field("general", description="Project identifier (e.g. fieldnation, personal)")
    category: str = Field("general", description="Category (architecture, preference, guideline, fact, etc.)")
    tags: List[str] = Field(default_factory=list, description="List of string tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional key-value metadata")
    conversation_id: Optional[str] = Field(None, description="Source conversation ID")


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = Field(None, description="Updated memory text")
    project: Optional[str] = Field(None, description="Updated project")
    category: Optional[str] = Field(None, description="Updated category")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    user_id: Optional[str] = Field(None, description="Filter by user ID or 'all'")
    project: Optional[str] = Field(None, description="Filter by project or 'all'")
    category: Optional[str] = Field(None, description="Filter by category or 'all'")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100, description="Max results to return")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold")


def setup_routes(mem0_service):
    @router.post("/memories", status_code=status.HTTP_201_CREATED)
    def create_memory(req: MemoryCreateRequest):
        try:
            return mem0_service.add_memory(
                content=req.content,
                user_id=req.user_id,
                project=req.project,
                category=req.category,
                tags=req.tags,
                metadata=req.metadata,
                conversation_id=req.conversation_id
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/memories")
    def list_memories(
        user_id: Optional[str] = Query(None),
        project: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0)
    ):
        return mem0_service.list_memories(
            user_id=user_id,
            project=project,
            category=category,
            limit=limit,
            offset=offset
        )

    @router.post("/memories/search")
    def search_memories(req: MemorySearchRequest):
        return mem0_service.search_memories(
            query=req.query,
            user_id=req.user_id,
            project=req.project,
            category=req.category,
            tags=req.tags,
            limit=req.limit,
            min_score=req.min_score
        )

    @router.get("/memories/{memory_id}")
    def get_memory(memory_id: str):
        mem = mem0_service.get_memory(memory_id)
        if not mem:
            raise HTTPException(status_code=404, detail="Memory not found")
        return mem

    @router.put("/memories/{memory_id}")
    def update_memory(memory_id: str, req: MemoryUpdateRequest):
        updated = mem0_service.update_memory(
            memory_id=memory_id,
            content=req.content,
            project=req.project,
            category=req.category,
            tags=req.tags,
            metadata=req.metadata
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Memory not found")
        return updated

    @router.delete("/memories/{memory_id}")
    def delete_memory(memory_id: str):
        success = mem0_service.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"success": True, "deleted_id": memory_id}

    @router.get("/memories/{memory_id}/history")
    def get_memory_history(memory_id: str):
        mem = mem0_service.get_memory(memory_id)
        if not mem:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"memory_id": memory_id, "history": mem.get("history", [])}

    @router.get("/stats")
    def get_stats():
        return mem0_service.get_stats()

    @router.post("/export")
    def export_data():
        return mem0_service.export_data()

    @router.post("/import")
    def import_data(payload: Dict[str, Any] = Body(...)):
        imported_count = mem0_service.import_data(payload)
        return {"success": True, "imported_count": imported_count}

    return router
