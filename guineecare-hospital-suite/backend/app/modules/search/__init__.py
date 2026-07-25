"""v1.2.0 — Global search module.

Single endpoint that searches across multiple resource types in parallel
(patients, lab orders, imaging orders, invoices) using LIKE patterns.

Why not PostgreSQL tsvector?
- The pilote runs on SQLite in dev mode and PostgreSQL 16 in prod.
- Implementing tsvector with GIN indexes would require divergent code paths.
- LIKE with proper indexes (already in place for patient_number, etc.)
  is fast enough for the expected data volume (<100k rows per table).
- The next iteration (v1.3) will add a real full-text search backend
  (Meilisearch or PostgreSQL tsvector + GIN).

The endpoint returns categorized results, capped at 10 per category and
50 total (configurable via ?limit).
"""
