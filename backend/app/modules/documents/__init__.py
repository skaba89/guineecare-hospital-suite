"""v1.2.0 — PDF document generation module.

Generates professional PDF documents for clinical and administrative
records (ordonnances, comptes rendus d'imagerie, résultats de laboratoire,
factures). PDFs are produced on-the-fly via ReportLab and streamed back
to the client as `application/pdf` responses.

All generated documents are journaled in `documents_generated` for audit
trail purposes (who generated what, when, for which patient).
"""
