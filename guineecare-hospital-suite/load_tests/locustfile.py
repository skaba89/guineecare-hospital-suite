"""GuinéeCare load tests with Locust.

Run from the project root:

    locust -f load_tests/locustfile.py --host http://localhost:8000

Then open http://localhost:8089 to drive the test from the web UI, or
run headless:

    locust -f load_tests/locustfile.py --host http://localhost:8000 \
        --headless -u 50 -r 5 -t 60s \
        --csv load_tests/results/locust_report

Scenarios:
    - Authenticated browse (default): each user logs in once, then browses
      patients, dashboard, notifications, audit log.
    - Login storm: each iteration performs a fresh login (rate-limited to
      5/min in prod — use only against dev).
    - Read-heavy: paginated GETs on /patients.

The tests are designed to be SAFE against a seeded dev DB
(ENVIRONMENT=local SEED_DEMO_DATA=true). They do NOT mutate data.
"""
from __future__ import annotations

import os
import random
import secrets
from typing import Any

from locust import HttpUser, between, events, task


# Test credentials (from seed data — see backend/app/db/seed.py)
DEFAULT_USERS = [
    ("admin@guineecare.com", "admin123"),
    ("admin.donka@chu-donka.gn", "admin123"),
    ("dr.diallo@chu-donka.gn", "doctor123"),
    ("inf.konde@chu-donka.gn", "nurse123"),
]


@events.init_command_line_parser.add_listener
def _add_args(parser: Any) -> None:
    parser.add_argument(
        "--test-password-override",
        type=str,
        default="",
        help="Override all test passwords (useful in non-seeded envs).",
    )


class GuineeCareUser(HttpUser):
    """A single simulated GuinéeCare user.

    Lifecycle:
      1. on_start: log in once and store the access_token in self.token.
      2. tasks: hit various read-only endpoints with the bearer token.
      3. on_stop: call /auth/logout (best effort).
    """

    wait_time = between(1.0, 3.5)  # realistic think time
    # NOTE: do NOT set `host` here — let it be provided via --host CLI arg
    # or the LOCUST_HOST env var. Setting it as a class attribute would
    # override the CLI value.

    # Default headers — overridden in on_start after successful login.
    headers: dict = {}

    def on_start(self) -> None:
        # Initialize per-instance state before anything else.
        self.token: str | None = None
        self.refresh: str | None = None
        self.role: str = "USER"
        self.headers: dict = {}

        pw_override = ""
        if self.environment.parsed_options:
            pw_override = getattr(
                self.environment.parsed_options, "test_password_override", ""
            ) or ""
        email, password = random.choice(DEFAULT_USERS)
        if pw_override:
            password = pw_override

        with self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="POST /auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"login failed: {resp.status_code} {resp.text[:200]}")
                return
            try:
                data = resp.json()
                self.token = data.get("access_token")
                self.refresh = data.get("refresh_token")
                self.role = (data.get("user") or {}).get("role", "USER")
            except Exception as e:
                resp.failure(f"login JSON parse error: {e}")
                return
            resp.success()

        if self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}

    def on_stop(self) -> None:
        if getattr(self, "token", None):
            self.client.post(
                "/api/v1/auth/logout",
                json={"access_token": self.token, "refresh_token": getattr(self, "refresh", None)},
                headers=self.headers,
                name="POST /auth/logout",
                catch_response=True,
            )

    # -----------------------------------------------------------------
    # Tasks — read-only to avoid mutating the seeded DB.
    # -----------------------------------------------------------------

    @task(5)
    def list_patients(self) -> None:
        """Browse the patient list with pagination."""
        page = random.randint(1, 3)
        self.client.get(
            f"/api/v1/patients?page={page}&page_size=20",
            headers=self.headers,
            name="GET /patients (paginated)",
        )

    @task(3)
    def get_patient_detail(self) -> None:
        """Fetch a single patient by ID (404 is OK — random UUID)."""
        # We don't know real IDs without a prior list call, so first list
        # then pick one.
        with self.client.get(
            "/api/v1/patients?page=1&page_size=20",
            headers=self.headers,
            name="GET /patients (for detail)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                return
            try:
                items = resp.json().get("data", [])
            except Exception:
                return
            if not items:
                return
            patient_id = random.choice(items).get("id")
        if patient_id:
            self.client.get(
                f"/api/v1/patients/{patient_id}",
                headers=self.headers,
                name="GET /patients/{id}",
            )

    @task(3)
    def dashboard(self) -> None:
        """Hit the reporting dashboard endpoint (heavy aggregations)."""
        self.client.get(
            "/api/v1/reporting/dashboard",
            headers=self.headers,
            name="GET /reporting/dashboard",
        )

    @task(2)
    def list_notifications(self) -> None:
        self.client.get(
            "/api/v1/notifications?page=1&page_size=10",
            headers=self.headers,
            name="GET /notifications",
        )

    @task(2)
    def unread_count(self) -> None:
        self.client.get(
            "/api/v1/notifications/unread-count",
            headers=self.headers,
            name="GET /notifications/unread-count",
        )

    @task(2)
    def list_users(self) -> None:
        """List users (admin-only — will 403 for doctors/nurses, that's OK)."""
        self.client.get(
            "/api/v1/users?page=1&page_size=20",
            headers=self.headers,
            name="GET /users",
        )

    @task(1)
    def me(self) -> None:
        self.client.get(
            "/api/v1/auth/me",
            headers=self.headers,
            name="GET /auth/me",
        )

    @task(1)
    def audit_logs(self) -> None:
        """Read the audit log (admin only)."""
        self.client.get(
            "/api/v1/audit/logs?page=1&page_size=20",
            headers=self.headers,
            name="GET /audit/logs",
        )

    @task(1)
    def health_ready(self) -> None:
        """Hit /health/ready — no auth required."""
        self.client.get("/health/ready", name="GET /health/ready")


class GuineeCareLoginStorm(HttpUser):
    """Login-storm scenario — every iteration performs a fresh login.

    Use this to stress-test the rate-limiter and DB connection pool. In
    production, /auth/login is rate-limited to 5/min per IP, so this will
    start receiving 429s quickly. In dev/test (rate-limiter disabled),
    it tests pure login throughput.
    """

    wait_time = between(0.5, 2.0)
    weight = 0  # disabled by default — enable with --tags login_storm

    @task
    def login(self) -> None:
        email, password = random.choice(DEFAULT_USERS)
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
            name="POST /auth/login (storm)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 429:
                # Expected in prod — don't fail the test on rate-limit.
                resp.success()
