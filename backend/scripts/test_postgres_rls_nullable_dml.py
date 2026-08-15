"""DML proof for nullable facility_id PostgreSQL RLS policy families.

This complements the visibility matrix in test_postgres_rls_nullable.py by
exercising INSERT / UPDATE / DELETE for the two reusable policy families:
shared national references and national-null operational records.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, text

from app.core.tenant import bind_tenant_context
from app.db.session import SessionLocal
from app.modules.billing.insurance_models import InsuranceProvider
from app.modules.quality.dashboard_models import QualityAlert
from test_postgres_rls_nullable import (
    A,
    AA,
    ALERT_B,
    ALERT_GLOBAL,
    B,
    INS_B,
    INS_GLOBAL,
    assert_blocked,
    seed,
)

INS_LOCAL = "10000000-0000-0000-0000-000000000710"
INS_GLOBAL_BAD = "90000000-0000-0000-0000-000000000710"
INS_CROSS_BAD = "20000000-0000-0000-0000-000000000710"
ALERT_LOCAL = "10000000-0000-0000-0000-000000000610"
ALERT_GLOBAL_BAD = "90000000-0000-0000-0000-000000000610"
ALERT_CROSS_BAD = "20000000-0000-0000-0000-000000000610"


def _cleanup(admin_url: str) -> None:
    engine = create_engine(admin_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM quality_alerts WHERE id IN (:a, :g, :b)"),
                {"a": ALERT_LOCAL, "g": ALERT_GLOBAL_BAD, "b": ALERT_CROSS_BAD},
            )
            conn.execute(
                text("DELETE FROM insurance_providers WHERE id IN (:a, :g, :b)"),
                {"a": INS_LOCAL, "g": INS_GLOBAL_BAD, "b": INS_CROSS_BAD},
            )
    finally:
        engine.dispose()


def _assert_zero_row_dml(db, sql: str, params: dict, message: str) -> None:
    result = db.execute(text(sql), params)
    assert result.rowcount == 0, message
    db.rollback()


def _exercise_shared_reference(db) -> None:
    """Facility ADMIN may mutate its override, never national/cross-tenant rows."""
    bind_tenant_context(db, SimpleNamespace(id=AA, role="ADMIN", facility_id=A))

    provider = InsuranceProvider(
        id=INS_LOCAL,
        facility_id=A,
        name="Local insurer DML",
        code="RLS2-DML-LOCAL",
        coverage_rate=55,
    )
    db.add(provider)
    db.commit()
    assert db.query(InsuranceProvider).filter(InsuranceProvider.id == INS_LOCAL).one().name == "Local insurer DML"

    provider = db.query(InsuranceProvider).filter(InsuranceProvider.id == INS_LOCAL).one()
    provider.name = "Local insurer DML updated"
    db.commit()
    assert db.query(InsuranceProvider).filter(InsuranceProvider.id == INS_LOCAL).one().name == "Local insurer DML updated"

    def insert_global():
        db.add(
            InsuranceProvider(
                id=INS_GLOBAL_BAD,
                facility_id=None,
                name="Illegal national insurer",
                code="RLS2-DML-GLOBAL-BAD",
                coverage_rate=50,
            )
        )
        db.commit()

    assert_blocked(insert_global)
    db.rollback()

    def insert_cross_tenant():
        db.add(
            InsuranceProvider(
                id=INS_CROSS_BAD,
                facility_id=B,
                name="Illegal cross-tenant insurer",
                code="RLS2-DML-CROSS-BAD",
                coverage_rate=50,
            )
        )
        db.commit()

    assert_blocked(insert_cross_tenant)
    db.rollback()

    _assert_zero_row_dml(
        db,
        "UPDATE insurance_providers SET name='ILLEGAL' WHERE id=:id",
        {"id": INS_GLOBAL},
        "facility ADMIN updated national insurance provider",
    )
    _assert_zero_row_dml(
        db,
        "UPDATE insurance_providers SET name='ILLEGAL' WHERE id=:id",
        {"id": INS_B},
        "facility ADMIN updated another tenant insurance provider",
    )
    _assert_zero_row_dml(
        db,
        "DELETE FROM insurance_providers WHERE id=:id",
        {"id": INS_GLOBAL},
        "facility ADMIN deleted national insurance provider",
    )
    _assert_zero_row_dml(
        db,
        "DELETE FROM insurance_providers WHERE id=:id",
        {"id": INS_B},
        "facility ADMIN deleted another tenant insurance provider",
    )

    deleted = (
        db.query(InsuranceProvider)
        .filter(InsuranceProvider.id == INS_LOCAL)
        .delete(synchronize_session=False)
    )
    assert deleted == 1, "facility ADMIN could not delete its own insurance override"
    db.commit()
    assert db.query(InsuranceProvider).filter(InsuranceProvider.id == INS_LOCAL).first() is None


def _exercise_operational(db) -> None:
    """Facility ADMIN may mutate owned operational rows; NULL stays national-only."""
    bind_tenant_context(db, SimpleNamespace(id=AA, role="ADMIN", facility_id=A))

    alert = QualityAlert(
        id=ALERT_LOCAL,
        facility_id=A,
        title="Local operational DML",
        status="OPEN",
        severity="HIGH",
    )
    db.add(alert)
    db.commit()
    assert db.query(QualityAlert).filter(QualityAlert.id == ALERT_LOCAL).one().status == "OPEN"

    alert = db.query(QualityAlert).filter(QualityAlert.id == ALERT_LOCAL).one()
    alert.status = "ACKNOWLEDGED"
    db.commit()
    assert db.query(QualityAlert).filter(QualityAlert.id == ALERT_LOCAL).one().status == "ACKNOWLEDGED"

    def insert_national_null():
        db.add(
            QualityAlert(
                id=ALERT_GLOBAL_BAD,
                facility_id=None,
                title="Illegal national operational alert",
                status="OPEN",
                severity="CRITICAL",
            )
        )
        db.commit()

    assert_blocked(insert_national_null)
    db.rollback()

    def insert_cross_tenant():
        db.add(
            QualityAlert(
                id=ALERT_CROSS_BAD,
                facility_id=B,
                title="Illegal cross-tenant operational alert",
                status="OPEN",
                severity="HIGH",
            )
        )
        db.commit()

    assert_blocked(insert_cross_tenant)
    db.rollback()

    _assert_zero_row_dml(
        db,
        "UPDATE quality_alerts SET status='CLOSED' WHERE id=:id",
        {"id": ALERT_GLOBAL},
        "facility ADMIN updated national quality alert",
    )
    _assert_zero_row_dml(
        db,
        "UPDATE quality_alerts SET status='CLOSED' WHERE id=:id",
        {"id": ALERT_B},
        "facility ADMIN updated another tenant quality alert",
    )
    _assert_zero_row_dml(
        db,
        "DELETE FROM quality_alerts WHERE id=:id",
        {"id": ALERT_GLOBAL},
        "facility ADMIN deleted national quality alert",
    )
    _assert_zero_row_dml(
        db,
        "DELETE FROM quality_alerts WHERE id=:id",
        {"id": ALERT_B},
        "facility ADMIN deleted another tenant quality alert",
    )

    deleted = (
        db.query(QualityAlert)
        .filter(QualityAlert.id == ALERT_LOCAL)
        .delete(synchronize_session=False)
    )
    assert deleted == 1, "facility ADMIN could not delete its own quality alert"
    db.commit()
    assert db.query(QualityAlert).filter(QualityAlert.id == ALERT_LOCAL).first() is None


def main() -> None:
    admin_url = os.environ["RLS_ADMIN_DATABASE_URL"]
    _cleanup(admin_url)
    seed(admin_url)
    db = SessionLocal()
    try:
        _exercise_shared_reference(db)
        _exercise_operational(db)
    finally:
        db.close()
        _cleanup(admin_url)

    print("PASS: nullable RLS DML permits owned rows and blocks national/cross-tenant writes")


if __name__ == "__main__":
    main()
