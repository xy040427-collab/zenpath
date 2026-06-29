from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

try:
    from rag.intent_router import ChsiIntentRouter
except ImportError:  # pragma: no cover - allows direct script execution from project root.
    from backend.rag.intent_router import ChsiIntentRouter


EXPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "export"
DEFAULT_VECTOR_DIR = EXPORT_DIR / "vector_store" / "faiss"
DEFAULT_MANIFEST = EXPORT_DIR / "embedding_manifest.json"


def read_faiss_index(path: Path) -> faiss.Index:
    try:
        return faiss.read_index(str(path))
    except RuntimeError:
        if not path.exists():
            raise
        data = np.frombuffer(path.read_bytes(), dtype="uint8")
        return faiss.deserialize_index(data)


def load_sentence_transformer(model_name: str) -> SentenceTransformer:
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return SentenceTransformer(model_name)


def as_list(value: Any) -> list[Any] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


class ChsiVectorRetriever:
    def __init__(
        self,
        vector_dir: Path = DEFAULT_VECTOR_DIR,
        manifest_path: Path = DEFAULT_MANIFEST,
        model_name: str | None = None,
    ):
        self.vector_dir = Path(vector_dir)
        self.manifest_path = Path(manifest_path)
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8")) if self.manifest_path.exists() else {}
        self.model_name = model_name or self.manifest.get("embedding_model") or "BAAI/bge-small-zh-v1.5"
        self.index = read_faiss_index(self.vector_dir / "index.faiss")
        self.docstore = [
            json.loads(line)
            for line in (self.vector_dir / "docstore.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.id_map = json.loads((self.vector_dir / "id_map.json").read_text(encoding="utf-8"))
        if self.index.ntotal != len(self.docstore):
            raise RuntimeError(f"index/docstore mismatch: {self.index.ntotal} vs {len(self.docstore)}")
        self.model = load_sentence_transformer(self.model_name)
        self._vectors: np.ndarray | None = None
        self.school_names = sorted({row["metadata"].get("school_name") for row in self.docstore if row["metadata"].get("school_name")}, key=len, reverse=True)
        self.major_names = sorted({row["metadata"].get("major_name") for row in self.docstore if row["metadata"].get("major_name")}, key=len, reverse=True)
        self.router = ChsiIntentRouter(self.school_names, self.major_names)

    @property
    def vectors(self) -> np.ndarray:
        if self._vectors is None:
            try:
                self._vectors = self.index.reconstruct_n(0, self.index.ntotal)
            except Exception:
                arr = np.zeros((self.index.ntotal, self.index.d), dtype="float32")
                for i in range(self.index.ntotal):
                    arr[i] = self.index.reconstruct(i)
                self._vectors = arr
            self._vectors = np.asarray(self._vectors, dtype="float32")
        return self._vectors

    def route(self, query: str, **filters: Any) -> dict[str, Any]:
        return self.router.route(query, **filters).to_dict()

    def search(self, query: str, top_k: int = 5, use_router: bool = True, **filters: Any) -> dict[str, Any]:
        routed = self.route(query, **filters) if use_router else {"query": query, "intent": "manual", "filters": filters, "missing_data": [], "warnings": []}
        metadata_filters = routed.get("filters") or {}
        if routed.get("intent") == "employment_query":
            return {
                "query": query,
                "intent": routed["intent"],
                "filters": metadata_filters,
                "results": [],
                "missing_data": routed.get("missing_data", ["employment_report"]),
                "warnings": routed.get("warnings", []),
            }

        candidates = self._candidate_indices(metadata_filters)
        if not candidates:
            return {
                "query": query,
                "intent": routed.get("intent"),
                "filters": metadata_filters,
                "results": [],
                "missing_data": routed.get("missing_data", []),
                "warnings": routed.get("warnings", []),
            }

        query_vector = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        query_vector = np.asarray(query_vector, dtype="float32")[0]
        cand_array = np.asarray(candidates, dtype=np.int64)
        cand_vectors = self.vectors[cand_array]
        scores = cand_vectors @ query_vector
        top_n = min(max(top_k * 5, top_k), len(candidates))
        best_local = np.argpartition(-scores, top_n - 1)[:top_n]
        ordered = sorted(best_local, key=lambda i: self._rerank_score(float(scores[i]), self.docstore[candidates[int(i)]], query), reverse=True)

        results = []
        for local_idx in ordered[:top_k]:
            faiss_id = candidates[int(local_idx)]
            row = self.docstore[faiss_id]
            score = float(scores[int(local_idx)])
            meta = row.get("metadata") or {}
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "faiss_id": faiss_id,
                    "score": score,
                    "rerank_score": self._rerank_score(score, row, query),
                    "content": row["content"],
                    "source_url": meta.get("source_url", ""),
                    "doc_type": meta.get("doc_type", ""),
                    "school_name": meta.get("school_name", ""),
                    "title": meta.get("title", ""),
                    "section": meta.get("section", ""),
                    "metadata": meta,
                }
            )
        return {
            "query": query,
            "intent": routed.get("intent"),
            "filters": metadata_filters,
            "results": results,
            "missing_data": routed.get("missing_data", []),
            "warnings": routed.get("warnings", []),
        }

    def _candidate_indices(self, filters: dict[str, Any]) -> list[int]:
        candidates: list[int] = []
        for idx, row in enumerate(self.docstore):
            metadata = row.get("metadata") or {}
            if self._matches(metadata, filters):
                candidates.append(idx)
        return candidates

    @staticmethod
    def _matches(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if key not in {"school_name", "major_name", "doc_type", "scope", "year", "source_type", "source_url", "section"}:
                continue
            expected_values = as_list(expected)
            if expected_values is None:
                continue
            actual = metadata.get(key)
            if key == "year" and actual is not None:
                try:
                    actual = int(actual)
                    expected_values = [int(value) for value in expected_values]
                except Exception:
                    pass
            if actual not in expected_values:
                return False
        return True

    @staticmethod
    def _rerank_score(score: float, row: dict[str, Any], query: str) -> float:
        metadata = row.get("metadata") or {}
        title = metadata.get("title") or ""
        section = metadata.get("section") or ""
        content = row.get("content") or ""
        boost = 0.0
        for token in (metadata.get("school_name"), metadata.get("major_name"), section):
            if token and token in query:
                boost += 0.03
        if title and any(part and part in query for part in title.replace("：", " ").split()):
            boost += 0.02
        if "就业方向" in query and "就业" in content[:200]:
            boost += 0.03
        return score + boost


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--school-name")
    parser.add_argument("--major-name")
    parser.add_argument("--doc-type", action="append")
    parser.add_argument("--scope", action="append")
    parser.add_argument("--year", type=int)
    parser.add_argument("--source-type")
    parser.add_argument("--vector-dir", type=Path, default=DEFAULT_VECTOR_DIR)
    args = parser.parse_args()
    retriever = ChsiVectorRetriever(vector_dir=args.vector_dir)
    result = retriever.search(
        args.query,
        top_k=args.top_k,
        school_name=args.school_name,
        major_name=args.major_name,
        doc_type=args.doc_type,
        scope=args.scope,
        year=args.year,
        source_type=args.source_type,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
