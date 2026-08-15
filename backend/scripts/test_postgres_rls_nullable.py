"""PostgreSQL integration tests for nullable facility_id RLS policies."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT)) if str(BACKEND_ROOT) not in sys.path else None

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker

from app.core.tenant import bind_tenant_context
from app.db.session import SessionLocal
from app.modules.auth.models import DataBreach
from app.modules.billing.insurance_models import InsuranceProvider
from app.modules.departments.models import Department  # noqa: F401
from app.modules.facilities.models import Facility
from app.modules.notifications.models import Notification
from app.modules.notifications.sms_models import SmsMessage, SmsRoutingRule
from app.modules.quality.dashboard_models import QualityAlert, QualityThreshold
from app.modules.quality.models import QualityIndicator
from app.modules.user_profile.models import UserFeedback
from app.modules.users.models import User

A = "10000000-0000-0000-0000-000000000001"
B = "20000000-0000-0000-0000-000000000001"
UA = "10000000-0000-0000-0000-000000000101"
AA = "10000000-0000-0000-0000-000000000102"
UB = "20000000-0000-0000-0000-000000000101"
FA = "10000000-0000-0000-0000-000000000201"
FB = "20000000-0000-0000-0000-000000000201"
NA = "10000000-0000-0000-0000-000000000301"
NB = "20000000-0000-0000-0000-000000000301"
BA = "10000000-0000-0000-0000-000000000401"
BB = "20000000-0000-0000-0000-000000000401"
BN = "90000000-0000-0000-0000-000000000401"

IND_A = "10000000-0000-0000-0000-000000000501"
IND_B = "20000000-0000-0000-0000-000000000501"
TH_GLOBAL = "90000000-0000-0000-0000-000000000501"
TH_A = "10000000-0000-0000-0000-000000000502"
TH_B = "20000000-0000-0000-0000-000000000502"
ALERT_GLOBAL = "90000000-0000-0000-0000-000000000601"
ALERT_A = "10000000-0000-0000-0000-000000000601"
ALERT_B = "20000000-0000-0000-0000-000000000601"

INS_GLOBAL = "90000000-0000-0000-0000-000000000701"
INS_A = "10000000-0000-0000-0000-000000000701"
INS_B = "20000000-0000-0000-0000-000000000701"

RULE_GLOBAL = "90000000-0000-0000-0000-000000000801"
RULE_A = "10000000-0000-0000-0000-000000000801"
RULE_B = "20000000-0000-0000-0000-000000000801"
SMS_GLOBAL = "90000000-0000-0000-0000-000000000901"
SMS_A = "10000000-0000-0000-0000-000000000901"
SMS_B = "20000000-0000-0000-0000-000000000901"


def _delete_ids(db, model, values):
    db.query(model).filter(model.id.in_(values)).delete(synchronize_session=False)


def seed(url):
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        _delete_ids(db, SmsMessage, [SMS_GLOBAL, SMS_A, SMS_B])
        _delete_ids(db, SmsRoutingRule, [RULE_GLOBAL, RULE_A, RULE_B])
        _delete_ids(db, QualityAlert, [ALERT_GLOBAL, ALERT_A, ALERT_B])
        _delete_ids(db, QualityThreshold, [TH_GLOBAL, TH_A, TH_B])
        _delete_ids(db, QualityIndicator, [IND_A, IND_B])
        _delete_ids(db, InsuranceProvider, [INS_GLOBAL, INS_A, INS_B])
        for model, values in [
            (Notification, [NA, NB]),
            (UserFeedback, [FA, FB]),
            (DataBreach, [BA, BB, BN]),
        ]:
            _delete_ids(db, model, values)
        _delete_ids(db, User, [UA, AA, UB])
        _delete_ids(db, Facility, [A, B])
        db.commit()

        db.add_all([
            Facility(id=A, code="RLS2-A", name="RLS2 A"),
            Facility(id=B, code="RLS2-B", name="RLS2 B"),
        ])
        db.flush()
        db.add_all([
            User(id=UA, facility_id=A, email="rls2-a@test", password_hash="x", first_name="A", last_name="Doctor", role="DOCTOR", is_active=True),
            User(id=AA, facility_id=A, email="rls2-admin@test", password_hash="x", first_name="A", last_name="Admin", role="ADMIN", is_active=True),
            User(id=UB, facility_id=B, email="rls2-b@test", password_hash="x", first_name="B", last_name="Doctor", role="DOCTOR", is_active=True),
        ])
        db.flush()
        db.add_all([
            QualityIndicator(id=IND_A, facility_id=A, code="RLS2-A-IND", name="RLS2 indicator A"),
            QualityIndicator(id=IND_B, facility_id=B, code="RLS2-B-IND", name="RLS2 indicator B"),
        ])
        db.flush()

        db.add_all([
            UserFeedback(id=FA, user_id=UA, facility_id=A, category="bug", message="A feedback"),
            UserFeedback(id=FB, user_id=UB, facility_id=B, category="bug", message="B feedback"),
            Notification(id=NA, recipient_id=UA, facility_id=A, category="system", title="A notice"),
            Notification(id=NB, recipient_id=UB, facility_id=B, category="system", title="B notice"),
            DataBreach(id=BA, facility_id=A, reported_by=AA, title="A breach", description="A", severity="HIGH"),
            DataBreach(id=BB, facility_id=B, reported_by=UB, title="B breach", description="B", severity="HIGH"),
            DataBreach(id=BN, facility_id=None, reported_by=None, title="National breach", description="N", severity="CRITICAL"),
            InsuranceProvider(id=INS_GLOBAL, facility_id=None, name="National insurer", code="RLS2-INS-G", coverage_rate=80),
            InsuranceProvider(id=INS_A, facility_id=A, name="Insurer A", code="RLS2-INS-A", coverage_rate=70),
            InsuranceProvider(id=INS_B, facility_id=B, name="Insurer B", code="RLS2-INS-B", coverage_rate=60),
            QualityThreshold(id=TH_GLOBAL, facility_id=None, indicator_id=IND_A, comparator="GT", threshold_value="5", severity="HIGH"),
            QualityThreshold(id=TH_A, facility_id=A, indicator_id=IND_A, comparator="GT", threshold_value="6", severity="HIGH"),
            QualityThreshold(id=TH_B, facility_id=B, indicator_id=IND_B, comparator="GT", threshold_value="7", severity="HIGH"),
            SmsRoutingRule(id=RULE_GLOBAL, facility_id=None, category="rls2_global", channels="in_app,sms", min_priority="high", enabled=True),
            SmsRoutingRule(id=RULE_A, facility_id=A, category="rls2_a", channels="sms", min_priority="normal", enabled=True),
            SmsRoutingRule(id=RULE_B, facility_id=B, category="rls2_b", channels="sms", min_priority="normal", enabled=True),
            QualityAlert(id=ALERT_GLOBAL, facility_id=None, title="National quality alert", status="OPEN", severity="CRITICAL"),
            QualityAlert(id=ALERT_A, facility_id=A, title="A quality alert", status="OPEN", severity="HIGH"),
            QualityAlert(id=ALERT_B, facility_id=B, title="B quality alert", status="OPEN", severity="HIGH"),
            SmsMessage(id=SMS_GLOBAL, facility_id=None, provider_code="mock", recipient_phone="+224600000001", body="National SMS", category="system", priority="high", status="SENT", attempts=1),
            SmsMessage(id=SMS_A, facility_id=A, provider_code="mock", recipient_phone="+224600000002", body="A SMS", category="system", priority="normal", status="SENT", attempts=1),
            SmsMessage(id=SMS_B, facility_id=B, provider_code="mock", recipient_phone="+224600000003", body="B SMS", category="system", priority="normal", status="SENT", attempts=1),
        ])
        db.commit()
    finally:
        db.close()
        engine.dispose()


def ids(db, model):
    return {row.id for row in db.query(model).all()}


def assert_blocked(fn):
    blocked = False
    try:
        fn()
    except DBAPIError:
        blocked = True
    assert blocked


def assert_global_update_is_blocked(db, table: str, row_id: str, column: str, value: str):
    result = db.execute(
        text(f"UPDATE {table} SET {column} = :value WHERE id = :id"),
        {"id": row_id, "value": value},
    )
    assert result.rowcount == 0, f"facility role updated global row in {table}"
    db.rollback()


def main():
    admin = os.environ["RLS_ADMIN_DATABASE_URL"]
    seed(admin)
    db = SessionLocal()
    try:
        for model in [
            UserFeedback,
            Notification,
            DataBreach,
            InsuranceProvider,
            QualityThreshold,
            SmsRoutingRule,
            QualityAlert,
            SmsMessage,
        ]:
            assert ids(db, model) == set(), f"unauthenticated access leaked {model.__tablename__}"

        bind_tenant_context(db, SimpleNamespace(id=UA, role="DOCTOR", facility_id=A))
        assert ids(db, UserFeedback) == {FA}
        assert ids(db, Notification) == {NA}
        assert ids(db, DataBreach) == {BA}
        assert ids(db, InsuranceProvider) == {INS_GLOBAL, INS_A}
        assert ids(db, QualityThreshold) == {TH_GLOBAL, TH_A}
        assert ids(db, SmsRoutingRule) == {RULE_GLOBAL, RULE_A}
        assert ids(db, QualityAlert) == {ALERT_A}
        assert ids(db, SmsMessage) == {SMS_A}

        assert_global_update_is_blocked(db, "insurance_providers", INS_GLOBAL, "name", "ILLEGAL")
        assert_global_update_is_blocked(db, "quality_thresholds", TH_GLOBAL, "threshold_value", "999")
        assert_global_update_is_blocked(db, "sms_routing_rules", RULE_GLOBAL, "description", "ILLEGAL")

        def insert_illegal_global_provider():
            db.execute(
                text("""
                    INSERT INTO insurance_providers
                        (id, facility_id, name, code, coverage_rate, status, created_at)
                    VALUES
                        ('90000000-0000-0000-0000-000000000799', NULL,
                         'Illegal global insurer', 'RLS2-ILLEGAL', 50, 'ACTIVE', NOW())
                """)
            )
            db.commit()

        assert_blocked(insert_illegal_global_provider)
        db.rollback()

        feedback = db.query(UserFeedback).filter(UserFeedback.id == FA).one()
        feedback.status = "resolved"
        assert_blocked(db.commit)
        db.rollback()

        bind_tenant_context(db, SimpleNamespace(id=AA, role="ADMIN", facility_id=A))
        assert ids(db, UserFeedback) == {FA}
        feedback = db.query(UserFeedback).filter(UserFeedback.id == FA).one()
        feedback.status = "resolved"
        db.commit()
        assert ids(db, Notification) == set(), "facility admin must not read another user notification"
        assert ids(db, DataBreach) == {BA}
        assert ids(db, InsuranceProvider) == {INS_GLOBAL, INS_A}
        assert ids(db, QualityAlert) == {ALERT_A}
        assert ids(db, SmsMessage) == {SMS_A}

        bind_tenant_context(
            db,
            SimpleNamespace(
                id="90000000-0000-0000-0000-000000000999",
                role="SUPER_ADMIN",
                facility_id=None,
            ),
        )
        assert ids(db, UserFeedback) == {FA, FB}
        assert ids(db, Notification) == {NA, NB}
        assert ids(db, DataBreach) == {BA, BB, BN}
        assert ids(db, InsuranceProvider) == {INS_GLOBAL, INS_A, INS_B}
        assert ids(db, QualityThreshold) == {TH_GLOBAL, TH_A, TH_B}
        assert ids(db, SmsRoutingRule) == {RULE_GLOBAL, RULE_A, RULE_B}
        assert ids(db, QualityAlert) == {ALERT_GLOBAL, ALERT_A, ALERT_B}
        assert ids(db, SmsMessage) == {SMS_GLOBAL, SMS_A, SMS_B}

        row = db.execute(
            text(
                "SELECT current_setting('app.current_role', true), "
                "current_setting('app.current_user_id', true)"
            )
        ).one()
        assert row[0] == "SUPER_ADMIN" and row[1]
    finally:
        db.close()

    print("PASS: nullable facility_id RLS policies enforce tenant, shared-reference and national scopes")


if __name__ == "__main__":
    main()
