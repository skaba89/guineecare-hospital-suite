"""national multi-country facility foundation

Revision ID: 0030_national_multicountry_foundation
Revises: 0029_v291_insurance
Create Date: 2026-08-11

Adds a country-aware administrative hierarchy and interoperability identifiers
without removing the existing Guinea-specific region/prefecture/commune fields.
Existing Guinea data is backfilled into admin_level_1..3.
"""
from alembic import op
import sqlalchemy as sa


revision = "0030_national_multicountry_foundation"
down_revision = "0029_v291_insurance"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "facilities",
        sa.Column("country_code", sa.String(2), nullable=False, server_default="GN"),
    )
    op.add_column("facilities", sa.Column("admin_level_1", sa.String(150), nullable=True))
    op.add_column("facilities", sa.Column("admin_level_2", sa.String(150), nullable=True))
    op.add_column("facilities", sa.Column("admin_level_3", sa.String(150), nullable=True))
    op.add_column("facilities", sa.Column("admin_level_4", sa.String(150), nullable=True))
    op.add_column("facilities", sa.Column("health_district", sa.String(150), nullable=True))
    op.add_column("facilities", sa.Column("facility_type_code", sa.String(50), nullable=True))
    op.add_column("facilities", sa.Column("dhis2_org_unit_id", sa.String(128), nullable=True))
    op.add_column("facilities", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("facilities", sa.Column("longitude", sa.Float(), nullable=True))

    # Preserve the current Guinea hierarchy in the generic representation.
    op.execute(
        "UPDATE facilities SET admin_level_1 = region "
        "WHERE admin_level_1 IS NULL AND region IS NOT NULL"
    )
    op.execute(
        "UPDATE facilities SET admin_level_2 = prefecture "
        "WHERE admin_level_2 IS NULL AND prefecture IS NOT NULL"
    )
    op.execute(
        "UPDATE facilities SET admin_level_3 = commune "
        "WHERE admin_level_3 IS NULL AND commune IS NOT NULL"
    )

    op.create_index("ix_facilities_country_code", "facilities", ["country_code"])
    op.create_index("ix_facilities_admin_level_1", "facilities", ["admin_level_1"])
    op.create_index("ix_facilities_admin_level_2", "facilities", ["admin_level_2"])
    op.create_index("ix_facilities_admin_level_3", "facilities", ["admin_level_3"])
    op.create_index("ix_facilities_admin_level_4", "facilities", ["admin_level_4"])
    op.create_index("ix_facilities_health_district", "facilities", ["health_district"])
    op.create_index("ix_facilities_facility_type_code", "facilities", ["facility_type_code"])
    op.create_index("ix_facilities_dhis2_org_unit_id", "facilities", ["dhis2_org_unit_id"])


def downgrade():
    op.drop_index("ix_facilities_dhis2_org_unit_id", table_name="facilities")
    op.drop_index("ix_facilities_facility_type_code", table_name="facilities")
    op.drop_index("ix_facilities_health_district", table_name="facilities")
    op.drop_index("ix_facilities_admin_level_4", table_name="facilities")
    op.drop_index("ix_facilities_admin_level_3", table_name="facilities")
    op.drop_index("ix_facilities_admin_level_2", table_name="facilities")
    op.drop_index("ix_facilities_admin_level_1", table_name="facilities")
    op.drop_index("ix_facilities_country_code", table_name="facilities")

    op.drop_column("facilities", "longitude")
    op.drop_column("facilities", "latitude")
    op.drop_column("facilities", "dhis2_org_unit_id")
    op.drop_column("facilities", "facility_type_code")
    op.drop_column("facilities", "health_district")
    op.drop_column("facilities", "admin_level_4")
    op.drop_column("facilities", "admin_level_3")
    op.drop_column("facilities", "admin_level_2")
    op.drop_column("facilities", "admin_level_1")
    op.drop_column("facilities", "country_code")
