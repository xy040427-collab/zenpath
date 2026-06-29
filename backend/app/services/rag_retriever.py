from __future__ import annotations

from pathlib import Path
from typing import Any

from rag.evidence_packer import pack_evidence
from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever


class ChsiRagService:
    def __init__(self, vector_dir: str | Path | None = None):
        self.retriever = ChsiVectorRetriever(vector_dir=Path(vector_dir)) if vector_dir else ChsiVectorRetriever()

    def search(self, query: str, top_k: int = 5, **filters: Any) -> dict[str, Any]:
        return self.retriever.search(query, top_k=top_k, **filters)

    def evidence(self, query: str, top_k: int = 5, **filters: Any) -> dict[str, Any]:
        return pack_evidence(self.search(query, top_k=top_k, **filters), max_items=top_k)
