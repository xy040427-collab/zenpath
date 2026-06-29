from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter, Query
    from pydantic import BaseModel
except Exception:  # pragma: no cover - lets the module be imported without FastAPI installed.
    APIRouter = None
    Query = None
    BaseModel = object

from app.services.rag_retriever import ChsiRagService


if APIRouter is not None:
    router = APIRouter(prefix="/api/rag/chsi", tags=["CHSI RAG"])
    _service: ChsiRagService | None = None

    def get_service() -> ChsiRagService:
        global _service
        if _service is None:
            _service = ChsiRagService()
        return _service

    class EvidenceRequest(BaseModel):
        query: str
        top_k: int = 5
        school_name: str | None = None
        major_name: str | None = None
        doc_type: str | list[str] | None = None
        scope: str | list[str] | None = None
        year: int | None = None

    @router.get("/search")
    def search(
        query: str,
        top_k: int = 5,
        school_name: str | None = None,
        major_name: str | None = None,
        doc_type: str | None = None,
        scope: str | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        result = get_service().search(
            query=query,
            top_k=top_k,
            school_name=school_name,
            major_name=major_name,
            doc_type=doc_type,
            scope=scope,
            year=year,
        )
        # Transform results to match the expected response format
        clean_results = []
        for item in result.get("results", []):
            clean_results.append({
                "chunk_id": item.get("chunk_id"),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "doc_type": item.get("doc_type", ""),
                "school_name": item.get("school_name", ""),
                "major_name": item.get("metadata", {}).get("major_name"),
                "source_url": item.get("source_url", ""),
                "score": round(item.get("score", 0), 4),
            })
        return {
            "success": True,
            "query": result.get("query", query),
            "top_k": top_k,
            "results": clean_results,
            "warnings": result.get("warnings", []),
        }

    @router.post("/evidence")
    def evidence(request: EvidenceRequest) -> dict[str, Any]:
        result = get_service().evidence(
            query=request.query,
            top_k=request.top_k,
            school_name=request.school_name,
            major_name=request.major_name,
            doc_type=request.doc_type,
            scope=request.scope,
            year=request.year,
        )
        return {"success": True, **result}
else:
    router = None
