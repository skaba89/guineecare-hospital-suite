"""add facility.commune + indexes region/prefecture v2.5.0 — Phase 5 pilotage national

Revision ID: 0025_phase5_national_reporting
Revises: 0024_phase4_parcours_metiers
Create Date: 2026-07-05

Phase 5 — Pilotage national et reporting santé Guinée.

Ajoute :
- facilities.commune (VARCHAR 150) pour hiérarchie administrative complète
  Région > Préfecture > Commune > Quartier (Guinée)
- Index sur facilities.region et facilities.prefecture (pour filtres rapides
  dans les dashboards nationaux agrégés)
"""
from alembic import op
import sqlalchemy as sa


revision = "0025_phase5_national_reporting"
down_revision = "0024_phase4_parcours_metiers"
branch_labels = None
depends_on = None


def upgrade():
    # ── Facility : commune + indexes region/prefecture ──
    op.add_column(
        "facilities",
        sa.Column("commune", sa.String(150), nullable=True),
    )
    op.create_index(
        "ix_facilities_region",
        "facilities",
        ["region"],
    )
    op.create_index(
        "ix_facilities_prefecture",
        "facilities",
        ["prefecture"],
    )
    op.create_index(
        "ix_facilities_commune",
        "facilities",
        ["commune"],
    )


def downgrade():
    op.drop_index("ix_facilities_commune", table_name="facilities")
    op.drop_index("ix_facilities_prefecture", table_name="facilities")
    op.drop_index("ix_facilities_region", table_name="facilities")
    op.drop_column("facilities", "commune")
