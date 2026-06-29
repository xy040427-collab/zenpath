from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "export"
REPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "reports"

DEFAULT_INPUT = EXPORT_DIR / "rag_chunks_for_embedding_v2.jsonl"
DEFAULT_VECTOR_DIR = EXPORT_DIR / "vector_store" / "faiss"
DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
FAILED_LOG = REPORT_DIR / "chsi_embedding_failed.jsonl"
MANIFEST_PATH = EXPORT_DIR / "embedding_manifest.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_faiss_index(path: Path) -> faiss.Index:
    try:
        return faiss.read_index(str(path))
    except RuntimeError:
        if not path.exists():
            raise
        data = np.frombuffer(path.read_bytes(), dtype="uint8")
        return faiss.deserialize_index(data)


def write_faiss_index(index: faiss.Index, path: Path) -> None:
    try:
        faiss.write_index(index, str(path))
    except RuntimeError:
        data = faiss.serialize_index(index)
        path.write_bytes(data.tobytes())


def read_chunks(path: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            metadata = payload.get("metadata") or {}
            if metadata.get("quality_status") != "valid" or int(metadata.get("is_valid_for_rag", 0)) != 1:
                raise ValueError(f"Non-valid chunk in embedding input at line {line_no}: {payload.get('chunk_id')}")
            chunks.append(payload)
    return chunks


def load_existing(vector_dir: Path) -> tuple[faiss.Index | None, list[dict[str, Any]], dict[str, str]]:
    index_path = vector_dir / "index.faiss"
    docstore_path = vector_dir / "docstore.jsonl"
    id_map_path = vector_dir / "id_map.json"
    if not index_path.exists() or not docstore_path.exists() or not id_map_path.exists():
        return None, [], {}
    index = read_faiss_index(index_path)
    docs = [json.loads(line) for line in docstore_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    id_map = json.loads(id_map_path.read_text(encoding="utf-8"))
    if index.ntotal != len(docs) or index.ntotal != len(id_map):
        raise RuntimeError(
            f"Existing vector store is inconsistent: index={index.ntotal}, docstore={len(docs)}, id_map={len(id_map)}"
        )
    return index, docs, id_map


def write_docstore(path: Path, docs: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in docs:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_failed(rows: list[dict[str, Any]]) -> None:
    FAILED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FAILED_LOG.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def package_version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def build_vector_store(
    input_path: Path,
    vector_dir: Path,
    model_name: str,
    batch_size: int,
    checkpoint_every: int,
    resume: bool,
    rebuild: bool,
) -> dict[str, Any]:
    vector_dir.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = read_chunks(input_path)
    expected_count = len(chunks)

    if rebuild and vector_dir.exists():
        for child in vector_dir.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)

    existing_index, existing_docs, id_map = (None, [], {})
    if resume and not rebuild:
        existing_index, existing_docs, id_map = load_existing(vector_dir)
        if existing_index is not None and existing_index.ntotal == expected_count:
            manifest = write_manifest(
                input_path=input_path,
                vector_dir=vector_dir,
                model_name=model_name,
                dimension=existing_index.d,
                chunk_count=expected_count,
                vector_count=existing_index.ntotal,
                failed_count=0,
            )
            return {
                "status": "already_complete",
                "chunk_count": expected_count,
                "vector_count": existing_index.ntotal,
                "dimension": existing_index.d,
                "manifest": manifest,
            }

    start_at = len(existing_docs)
    if start_at:
        expected_prefix = [str(chunk["chunk_id"]) for chunk in chunks[:start_at]]
        existing_prefix = [str(row["chunk_id"]) for row in existing_docs]
        if expected_prefix != existing_prefix:
            raise RuntimeError("Existing docstore does not match current input prefix; run with --rebuild.")

    print(f"[load-model] {model_name}", flush=True)
    model = SentenceTransformer(model_name)
    dimension: int | None = existing_index.d if existing_index is not None else None
    index = existing_index
    docs = existing_docs
    failures: list[dict[str, Any]] = []

    pending = chunks[start_at:]
    total_batches = (len(pending) + batch_size - 1) // batch_size
    for batch_no, offset in enumerate(tqdm(range(0, len(pending), batch_size), desc="embedding", unit="batch"), start=1):
        batch = pending[offset : offset + batch_size]
        texts = [row["content"] for row in batch]
        try:
            vectors = model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            vectors = np.asarray(vectors, dtype="float32")
            if vectors.ndim != 2:
                raise RuntimeError(f"Unexpected embedding shape: {vectors.shape}")
            if dimension is None:
                dimension = int(vectors.shape[1])
                index = faiss.IndexFlatIP(dimension)
            if vectors.shape[1] != dimension:
                raise RuntimeError(f"Embedding dimension changed: expected {dimension}, got {vectors.shape[1]}")
            assert index is not None
            index.add(vectors)
            for row in batch:
                faiss_id = len(docs)
                chunk_id = str(row["chunk_id"])
                docs.append(
                    {
                        "faiss_id": faiss_id,
                        "chunk_id": row["chunk_id"],
                        "content": row["content"],
                        "content_hash": row.get("content_hash"),
                        "metadata": row["metadata"],
                    }
                )
                id_map[str(faiss_id)] = chunk_id
        except Exception as exc:
            for row in batch:
                failures.append(
                    {
                        "chunk_id": row.get("chunk_id"),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "created_at": now_iso(),
                    }
                )
            write_failed(failures)
            raise

        # Periodic checkpoints keep --resume useful without rewriting large files after every small batch.
        if batch_no % max(1, checkpoint_every) == 0 or batch_no == total_batches:
            assert index is not None
            write_faiss_index(index, vector_dir / "index.faiss")
            write_docstore(vector_dir / "docstore.jsonl", docs)
            (vector_dir / "id_map.json").write_text(json.dumps(id_map, ensure_ascii=False, indent=2), encoding="utf-8")

    write_failed(failures)
    assert index is not None
    manifest = write_manifest(
        input_path=input_path,
        vector_dir=vector_dir,
        model_name=model_name,
        dimension=int(index.d),
        chunk_count=expected_count,
        vector_count=int(index.ntotal),
        failed_count=len(failures),
    )
    return {
        "status": "built",
        "chunk_count": expected_count,
        "vector_count": int(index.ntotal),
        "dimension": int(index.d),
        "failed_count": len(failures),
        "manifest": manifest,
        "vector_dir": str(vector_dir),
    }


def write_manifest(
    input_path: Path,
    vector_dir: Path,
    model_name: str,
    dimension: int,
    chunk_count: int,
    vector_count: int,
    failed_count: int,
) -> str:
    manifest = {
        "embedding_model": model_name,
        "embedding_dimension": dimension,
        "chunk_count": chunk_count,
        "vector_count": vector_count,
        "failed_count": failed_count,
        "source_file": input_path.name,
        "source_file_sha256": sha256_file(input_path),
        "vector_store_type": "faiss",
        "vector_store_path": "vector_store/faiss",
        "created_at": now_iso(),
        "content_hash_strategy": "sha256",
        "metadata_version": "chsi_metadata_v2",
        "build_script": "backend/rag/indexing/build_chsi_vector_store.py",
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "dependencies": {
            "sentence-transformers": package_version("sentence-transformers"),
            "faiss-cpu": package_version("faiss-cpu"),
            "numpy": package_version("numpy"),
            "torch": package_version("torch"),
        },
        "files": {
            "index": str(vector_dir / "index.faiss"),
            "docstore": str(vector_dir / "docstore.jsonl"),
            "id_map": str(vector_dir / "id_map.json"),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(MANIFEST_PATH)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--vector-dir", type=Path, default=DEFAULT_VECTOR_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--checkpoint-every", type=int, default=20)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    result = build_vector_store(
        input_path=args.input,
        vector_dir=args.vector_dir,
        model_name=args.model,
        batch_size=max(1, args.batch_size),
        checkpoint_every=max(1, args.checkpoint_every),
        resume=args.resume,
        rebuild=args.rebuild,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
