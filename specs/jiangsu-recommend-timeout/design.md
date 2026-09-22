# Design
- Read source metadata directly for availability checks; do not instantiate embeddings/FAISS for metadata-only work.
- Keep optional AI enrichment outside the SQLite write transaction, with a 20-second budget. On timeout preserve the data-based report and record ai_generation_status=timeout.
- End the read transaction, acquire BEGIN IMMEDIATE for SQLite, then atomically persist session/application/recommendation/report records.
- Deduplicate identical in-flight frontend requests without caching completed results. Use a 60-second request budget to accommodate metadata/database work around AI enrichment.
- Preserve scoring, data sources, membership rules and database schema.
