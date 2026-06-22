"""add patient medical fields v1.7.1

Revision ID: 0021_patient_medical
Revises: 0019_rh_v2
Create Date: 2026-06-22

Ajoute 5 champs médicaux à la table `patients` :
- `blood_type` (String(10), NOT NULL, default 'NON_RENSEIGNE')
- `allergies` (Text, NOT NULL, default 'Non renseigné')
- `medical_history` (Text, NOT NULL, default 'Non renseigné')
- `current_medication` (Text, NOT NULL, default 'Non renseigné')
- `chronic_conditions` (Text, NOT NULL, default 'Non renseigné')

Stratégie : ne jamais laisser un champ vide. À la création, si le soignant
ne connaît pas l'information (fréquent en contexte d'urgence ou première
visite), la valeur par défaut "Non renseigné" est utilisée. Le soignant
pourra mettre à jour ces champs ultérieurement via le DPI patient.

Pour les patients existants (avant cette migration), les valeurs par défaut
sont appliquées rétroactivement.
"""
from alembic import op
import sqlalchemy as sa


revision = "0021_patient_medical"
down_revision = "0019_rh_v2"
branch_labels = None
depends_on = None


def upgrade():
    # blood_type
    op.add_column(
        "patients",
        sa.Column(
            "blood_type",
            sa.String(10),
            nullable=False,
            server_default="NON_RENSEIGNE",
        ),
    )

    # allergies
    op.add_column(
        "patients",
        sa.Column(
            "allergies",
            sa.Text(),
            nullable=False,
            server_default="Non renseigné",
        ),
    )

    # medical_history (antécédents)
    op.add_column(
        "patients",
        sa.Column(
            "medical_history",
            sa.Text(),
            nullable=False,
            server_default="Non renseigné",
        ),
    )

    # current_medication (traitement en cours)
    op.add_column(
        "patients",
        sa.Column(
            "current_medication",
            sa.Text(),
            nullable=False,
            server_default="Non renseigné",
        ),
    )

    # chronic_conditions (maladies chroniques)
    op.add_column(
        "patients",
        sa.Column(
            "chronic_conditions",
            sa.Text(),
            nullable=False,
            server_default="Non renseigné",
        ),
    )


def downgrade():
    op.drop_column("patients", "chronic_conditions")
    op.drop_column("patients", "current_medication")
    op.drop_column("patients", "medical_history")
    op.drop_column("patients", "allergies")
    op.drop_column("patients", "blood_type")
