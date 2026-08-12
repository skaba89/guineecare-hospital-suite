from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.db.base import Base

# Import all SQLAlchemy models so Alembic can detect metadata.
from app.modules.facilities.models import Facility  # noqa: F401
from app.modules.departments.models import Department  # noqa: F401
from app.modules.patients.models import Patient  # noqa: F401
from app.modules.admissions.models import Admission  # noqa: F401
from app.modules.users.models import User  # noqa: F401
from app.modules.rbac.models import Role, Permission, RolePermission  # noqa: F401
from app.modules.activity.models import ActivityEntry  # noqa: F401
from app.modules.emergency.models import EmergencyVisit  # noqa: F401
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement  # noqa: F401
from app.modules.laboratory.models import LabTest, LabOrder, LabResult  # noqa: F401
from app.modules.billing.models import TariffItem, Invoice, Payment  # noqa: F401
from app.modules.maternity.models import MaternityRecord, MaternityConsultation, DeliveryRecord  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            # Starting with revision 0031, FORCE ROW LEVEL SECURITY also
            # applies policies to ordinary table owners. Alembic is a trusted
            # control-plane process and must be able to perform national
            # backfills/repairs in future migrations. Give the migration
            # transaction an explicit national context rather than relying on
            # SUPERUSER/BYPASSRLS. A runtime application role should not own
            # the schema and therefore still cannot use Alembic for DDL.
            if connection.dialect.name == "postgresql":
                connection.execute(
                    text("SELECT set_config('app.is_super_admin', 'true', true)")
                )
                connection.execute(
                    text("SELECT set_config('app.current_facility_id', '', true)")
                )
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
