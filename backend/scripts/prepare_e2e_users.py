"""Prepare deterministic role accounts used by Playwright E2E tests.

This script is CI/test-only. It normalizes a small set of users in the
throw-away SQLite database created by the Playwright workflow. Production and
demo seed data are not modified.
"""

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.facilities.models import Facility
from app.modules.users.models import User


FIXTURES = (
    ("ph.bah@chu-donka.gn", "pharma123", "Mamadou", "Bah", "PHARMACIST"),
    ("lab.cisse@chu-donka.gn", "lab123", "Fatoumata", "Cissé", "LAB_TECH"),
    ("caissier.camara@chu-donka.gn", "cash123", "Sekou", "Camara", "CASHIER"),
)


def main() -> None:
    db = SessionLocal()
    try:
        facility = db.query(Facility).filter(Facility.code == "CHU-DONKA").first()
        if not facility:
            raise RuntimeError("CHU-DONKA is missing from E2E seed data")

        for email, password, first_name, last_name, role in FIXTURES:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    facility_id=facility.id,
                    password_hash=hash_password(password),
                    is_active=True,
                    failed_login_count=0,
                    locked_until=None,
                    last_disabled_at=None,
                )
                db.add(user)
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.role = role
                user.facility_id = facility.id
                user.password_hash = hash_password(password)
                user.is_active = True
                user.failed_login_count = 0
                user.locked_until = None
                user.last_disabled_at = None

        db.commit()
        print(f"Prepared {len(FIXTURES)} deterministic E2E role fixtures")
    finally:
        db.close()


if __name__ == "__main__":
    main()
