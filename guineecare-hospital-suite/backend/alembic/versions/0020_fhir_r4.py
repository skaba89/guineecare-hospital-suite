"""add FHIR R4 module v1.6.0 — CapabilityStatement + endpoint stub

Revision ID: 0020_fhir_r4
Revises: 0019_rh_v2
Create Date: 2026-06-21

Le module FHIR R4 v1.6 n'ajoute PAS de nouvelles tables — les ressources FHIR
sont générées à la volée à partir des modèles existants (Patient, Admission,
ClinicalNote, PatientMeasurement, LabResult, ImagingResult) via les fonctions
de `app.modules.fhir.conversions`.

Cette migration existe pour :
- Documenter l'activation du module FHIR dans l'historique Alembic.
- Préparer une future v1.7 qui pourrait ajouter une table `fhir_subscriptions`
  (gestion des abonnements FHIR Subscription pour push notifications).

Aucune opération DB réelle en v1.6.
"""
from alembic import op


revision = "0020_fhir_r4"
down_revision = "0019_rh_v2"
branch_labels = None
depends_on = None


def upgrade():
    # v1.6.0 — No DB changes. FHIR resources are generated on-the-fly.
    # Future v1.7 may add a `fhir_subscriptions` table for push notifications.
    pass


def downgrade():
    pass
