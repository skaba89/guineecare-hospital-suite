"""Real PostgreSQL integration checks for GuinéeCare facility RLS.

Required environment variables:
- DATABASE_URL: non-superuser/NOBYPASSRLS application role
- RLS_ADMIN_DATABASE_URL: migration/table owner connection used only for fixtures

This script intentionally does not use pytest because the normal pytest
conftest forces SQLite. It is executed by the dedicated GitHub Actions RLS job.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.core.tenant import bind_tenant_context
from app.db.session import SessionLocal
from app.modules.auth.dependencies import get_current_user
from app.modules.facilities.models import Facility
from app.modules.patients.models import Patient
from app.modules.users.models import User


FACILITY_A = "00000000-0000-0000-0000-00000000a001"
FACILITY_B = "00000000-0000-0000-0000-00000000b001"
PATIENT_A = "00000000-0000-0000-0000-00000000a101"
PATIENT_B = "00000000-0000-0000-0000-00000000b101"
PATIENT_BAD = "00000000-0000-0000-0000-00000000b199"
USER_A = "00000000-0000-0000-0000-00000000a201"
USER_EMAIL = "rls-ci-user@guineecare.test"
PREFIX = "RLS-CI-"


def _patient_numbers(db) -> set[str]:
    rows = (
        db.query(Patient)
        .filter(Patient.patient_number.like(f"{PREFIX}%"))
        .order_by(Patient.patient_number)
        .all()
    )
    return {row.patient_number for row in rows}


def _seed(admin_url: str) -> None:
    engine = create_engine(admin_url)
    AdminSession = sessionmaker(bind=engine)
    db = AdminSession()
    try:
        # Delete children/users before facilities so the fixture is idempotent.
        db.query(Patient).filter(Patient.patient_number.like(f"{PREFIX}%")).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.email == USER_EMAIL).delete(synchronize_session=False)
        db.query(Facility).filter(Facility.id.in_([FACILITY_A, FACILITY_B])).delete(
            synchronize_session=False
        )
        db.commit()

        db.add_all(
            [
                Facility(id=FACILITY_A, code="RLS-A", name="RLS Facility A"),
                Facility(id=FACILITY_B, code="RLS-B", name="RLS Facility B"),
            ]
        )
        db.flush()
        db.add(
            User(
                id=USER_A,
                facility_id=FACILITY_A,
                email=USER_EMAIL,
                password_hash="not-used-by-rls-test",
                first_name="RLS",
                last_name="User",
                role="DOCTOR",
                is_active=True,
            )
        )
        db.add_all(
            [
                Patient(
                    id=PATIENT_A,
                    facility_id=FACILITY_A,
                    patient_number=f"{PREFIX}A",
                    first_name="Alpha",
                    last_name="Tenant",
                ),
                Patient(
                    id=PATIENT_B,
                    facility_id=FACILITY_B,
                    patient_number=f"{PREFIX}B",
                    first_name="Beta",
                    last_name="Tenant",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()
        engine.dispose()


def _cleanup(admin_url: str) -> None:
    engine = create_engine(admin_url)
    AdminSession = sessionmaker(bind=engine)
    db = AdminSession()
    try:
        db.query(Patient).filter(Patient.patient_number.like(f"{PREFIX}%")).delete(
            synchronize_session=False
        )
        db.query(User).filter(User.email == USER_EMAIL).delete(synchronize_session=False)
        db.query(Facility).filter(Facility.id.in_([FACILITY_A, FACILITY_B])).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()
        engine.dispose()


def _assert_application_role_is_safe(db) -> None:
    row = db.execute(
        text(
            """
            SELECT r.rolsuper, r.rolbypassrls
            FROM pg_roles r
            WHERE r.rolname = current_user
            """
        )
    ).one()
    assert row.rolsuper is False, "Application role must not be SUPERUSER"
    assert row.rolbypassrls is False, "Application role must not have BYPASSRLS"


def _assert_authenticated_context_uses_database_identity() -> None:
    """A signed but stale/misleading JWT cannot select another tenant/role."""
    db = SessionLocal()
    try:
        # Deliberately mint claims that disagree with the database row. The
        # signed token says Facility B + SUPER_ADMIN, while USER_A is a DOCTOR
        # assigned to Facility A in the authoritative users table.
        misleading_token = create_access_token(
            subject=USER_A,
            facility_id=FACILITY_B,
            role="SUPER_ADMIN",
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=misleading_token,
        )

        current_user = get_current_user(credentials=credentials, db=db)
        assert current_user.facility_id == FACILITY_A
        assert current_user.role == "DOCTOR"
        assert _patient_numbers(db) == {f"{PREFIX}A"}, (
            "RLS followed JWT tenant/role claims instead of the database identity"
        )
    finally:
        db.close()


def _assert_all_required_facility_tables_are_forced(admin_url: str) -> None:
    engine = create_engine(admin_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT c.table_name, cls.relrowsecurity, cls.relforcerowsecurity
                FROM information_schema.columns c
                JOIN pg_class cls ON cls.relname = c.table_name
                JOIN pg_namespace ns ON ns.oid = cls.relnamespace
                                 AND ns.nspname = c.table_schema
                WHERE c.table_schema = current_schema()
                  AND c.column_name = 'facility_id'
                  AND c.is_nullable = 'NO'
                ORDER BY c.table_name
                """
            )
        ).all()

    assert rows, "Expected at least one strict facility-owned table"
    unprotected = [name for name, enabled, forced in rows if not enabled or not forced]
    assert not unprotected, f"Required facility tables without forced RLS: {unprotected}"
    engine.dispose()


def main() -> None:
    admin_url = os.environ["RLS_ADMIN_DATABASE_URL"]
    _seed(admin_url)

    try:
        db = SessionLocal()
        try:
            _assert_application_role_is_safe(db)

            # Fail closed: before authentication/context binding, the app role
            # cannot see any tenant-owned patient row.
            assert _patient_numbers(db) == set()

            # Facility A sees only its own data.
            bind_tenant_context(
                db, SimpleNamespace(role="DOCTOR", facility_id=FACILITY_A)
            )
            assert _patient_numbers(db) == {f"{PREFIX}A"}

            # Transaction-local PostgreSQL settings disappear at commit. The
            # Session after_begin listener must transparently restore them.
            db.commit()
            assert _patient_numbers(db) == {f"{PREFIX}A"}

            # WITH CHECK must reject a cross-tenant write even if application
            # code accidentally tries to create a row for Facility B.
            db.add(
                Patient(
                    id=PATIENT_BAD,
                    facility_id=FACILITY_B,
                    patient_number=f"{PREFIX}BAD",
                    first_name="Cross",
                    last_name="Tenant",
                )
            )
            blocked = False
            try:
                db.commit()
            except DBAPIError:
                blocked = True
                db.rollback()
            assert blocked, "Cross-tenant INSERT was not blocked by PostgreSQL RLS"

            # Session.info survives rollback; the next transaction must still
            # be restricted to Facility A.
            assert _patient_numbers(db) == {f"{PREFIX}A"}

            # Cross-tenant access is explicit and reserved for SUPER_ADMIN.
            bind_tenant_context(
                db, SimpleNamespace(role="SUPER_ADMIN", facility_id=None)
            )
            assert _patient_numbers(db) == {f"{PREFIX}A", f"{PREFIX}B"}
        finally:
            db.close()

        _assert_authenticated_context_uses_database_identity()
        _assert_all_required_facility_tables_are_forced(admin_url)
        print("PASS: PostgreSQL RLS is fail-closed and tenant isolation is enforced")
    finally:
        _cleanup(admin_url)


if __name__ == "__main__":
    main()
