# Acceptance — 2026-09-22
- Frontend npm run build: passed (existing bundle-size warning only).
- Three isolated SQLite regression tests passed: concurrent report writes without holding locks during AI, AI-timeout fallback persistence, source metadata preservation.
- Real browser recommendation request through Vite proxy: HTTP 200 in 27.182 seconds, success=true, 272 candidate groups, nonempty persisted report_id.
- React StrictMode page reload produced one recommendation POST, not two. Result page rendered and screenshot inspected.
- Retired the old Uvicorn process that was still draining a long request while holding a database writer lock. Only the replacement backend listens on port 3458.
- Real AI supplement exceeded the 20-second budget in this run. The data-based report was saved; this is not evidence of completed AI narrative generation or validated admissions predictions.
- No dependency, authentication, membership, schema or environment configuration changes. Existing unrelated untracked documents preserved.
