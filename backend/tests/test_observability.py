"""Tests for v0.7.0 observability endpoints — health, ready, metrics."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:

    def test_health_root(self):
        """GET /health returns 200 with status ok (backward compat)."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "guineecare-backend"
        assert "timestamp" in data

    def test_health_live(self):
        """GET /health/live returns 200 — liveness probe."""
        r = client.get("/health/live")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_health_ready_db_ok(self):
        """GET /health/ready returns 200 when DB is reachable."""
        r = client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "database" in data["checks"]
        assert data["checks"]["database"].startswith("ok")

    def test_health_ready_db_failure_returns_503(self):
        """GET /health/ready returns 503 when DB session.execute() raises.

        We override the get_db dependency to yield a mock session whose
        execute() raises an Exception, simulating a connection failure.
        """
        from unittest.mock import MagicMock
        from app.db.session import get_db

        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("DB down")

        def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            r = client.get("/health/ready")
            assert r.status_code == 503
            data = r.json()
            assert data["status"] == "degraded"
            assert "fail" in data["checks"]["database"]
        finally:
            app.dependency_overrides.pop(get_db, None)


class TestMetricsEndpoint:

    def test_metrics_returns_text_plain(self):
        """GET /metrics returns Prometheus text exposition format."""
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers["content-type"]

    def test_metrics_contains_expected_metric_names(self):
        r = client.get("/metrics")
        text = r.text
        # After a few requests, at least the in_flight gauge should be present
        assert "http_requests_in_flight" in text
        assert "# TYPE http_requests_in_flight gauge" in text

    def test_metrics_records_http_requests(self):
        """After hitting /health, the metrics should include a counter for it."""
        # Hit a known endpoint
        client.get("/health/live")
        client.get("/health/live")
        r = client.get("/metrics")
        # The metrics text should now include http_requests_total for /health/live
        assert "http_requests_total" in r.text
        # Note: /health/live is skipped from metrics, so we shouldn't see it tracked
        # Let's hit a real endpoint instead — /api/v1 needs auth, but /api/v1 root is open
        client.get("/api/v1")
        r = client.get("/metrics")
        assert "/api/v1" in r.text

    def test_metrics_in_flight_gauge_returns_to_zero(self):
        """In-flight requests should return to 0 after the request completes."""
        client.get("/health/live")
        client.get("/health/live")
        r = client.get("/metrics")
        # Parse the in_flight value
        for line in r.text.splitlines():
            if line.startswith("http_requests_in_flight ") and not line.startswith("#"):
                value = int(line.split()[-1])
                assert value == 0
                return
        # If we didn't find the line, the test fails
        assert False, "http_requests_in_flight metric not found"


class TestObservabilityNoAuth:
    """Observability endpoints should NOT require authentication."""

    def test_health_no_auth(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_live_no_auth(self):
        r = client.get("/health/live")
        assert r.status_code == 200

    def test_health_ready_no_auth(self):
        r = client.get("/health/ready")
        assert r.status_code == 200

    def test_metrics_no_auth(self):
        r = client.get("/metrics")
        assert r.status_code == 200
