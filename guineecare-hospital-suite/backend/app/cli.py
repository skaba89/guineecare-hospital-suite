"""GuinéeCare CLI — operational commands.

Usage:
    python -m app.cli create-superuser --email admin@hospital.gn \
        --first-name Admin --last-name Root [--facility-id <uuid>]

The CLI is the preferred way to create the first SUPER_ADMIN on a fresh
production deployment (A05-004 hardening — v0.9.0). The HTTP endpoint
`POST /users/bootstrap` is now gated by an `X-Bootstrap-Token` header in
non-local environments; the CLI uses the DB directly and bypasses HTTP.

The password is read from the `--password` flag (interactive prompt if
omitted) — never logged.
"""
from __future__ import annotations

import argparse
import getpass
import sys
from uuid import uuid4

from app.core.config import settings, validate_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.modules.users.models import User


def _ensure_schema() -> None:
    """Create tables if needed (idempotent)."""
    Base.metadata.create_all(bind=engine)


def _prompt_password() -> str:
    """Prompt for a password twice (confirmation) and validate complexity."""
    from app.modules.users.schemas import _validate_password_complexity

    while True:
        pw1 = getpass.getpass("Password: ")
        if not pw1:
            print("Password cannot be empty.", file=sys.stderr)
            continue
        pw2 = getpass.getpass("Confirm password: ")
        if pw1 != pw2:
            print("Passwords do not match. Try again.", file=sys.stderr)
            continue
        try:
            _validate_password_complexity(pw1)
        except ValueError as e:
            print(f"Password policy violation: {e}", file=sys.stderr)
            continue
        return pw1


def cmd_create_superuser(args: argparse.Namespace) -> int:
    """Create the first SUPER_ADMIN via DB direct (no HTTP)."""
    _ensure_schema()

    db = SessionLocal()
    try:
        existing_count = db.query(User).count()
        if existing_count > 0 and not args.force:
            print(
                "ERROR: users table is not empty. Use --force to create an "
                "additional SUPER_ADMIN.",
                file=sys.stderr,
            )
            return 2

        existing_email = db.query(User).filter(User.email == args.email).first()
        if existing_email:
            print(f"ERROR: email {args.email!r} already exists.", file=sys.stderr)
            return 3

        password = args.password or _prompt_password()

        facility_id = args.facility_id
        if not facility_id:
            # Look for an existing facility to attach the superuser to.
            from app.modules.facilities.models import Facility
            any_facility = db.query(Facility).first()
            if any_facility:
                facility_id = str(any_facility.id)
            # else leave None — SUPER_ADMIN doesn't require a facility.

        row = User(
            id=str(uuid4()),
            facility_id=facility_id,
            email=args.email,
            password_hash=hash_password(password),
            first_name=args.first_name,
            last_name=args.last_name,
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        print(f"✓ SUPER_ADMIN created: id={row.id} email={row.email}")
        if facility_id:
            print(f"  facility_id: {facility_id}")
        else:
            print("  facility_id: <none> (national superuser)")
        return 0
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="GuinéeCare operational CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_su = sub.add_parser(
        "create-superuser",
        help="Create the first SUPER_ADMIN via DB direct (bypasses HTTP bootstrap endpoint).",
    )
    p_su.add_argument("--email", required=True, help="Superuser email (unique)")
    p_su.add_argument("--first-name", required=True)
    p_su.add_argument("--last-name", required=True)
    p_su.add_argument(
        "--facility-id",
        default=None,
        help="Optional facility UUID. If omitted, attaches to the first existing facility.",
    )
    p_su.add_argument(
        "--password",
        default=None,
        help="Password. If omitted, prompts interactively (recommended).",
    )
    p_su.add_argument(
        "--force",
        action="store_true",
        help="Allow creation even when users already exist.",
    )
    p_su.set_defaults(func=cmd_create_superuser)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Validate config (AUTH_SECRET etc.) — but only warn in local.
    try:
        validate_settings()
    except SystemExit as e:
        # In non-local envs with bad config, validate_settings calls sys.exit.
        # We re-exit so the CLI also fails fast.
        return int(e.code or 1)
    except RuntimeError as e:
        print(f"WARNING: {e}", file=sys.stderr)

    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
