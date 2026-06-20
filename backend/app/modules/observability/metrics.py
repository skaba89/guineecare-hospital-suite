"""Lightweight in-process metrics collector — Prometheus text exposition format.

No external dependency. Designed for scraping by Prometheus/Grafana via /metrics.

Tracked metrics:
- http_requests_total{method, path_template, status}  — counter
- http_request_duration_seconds{method, path_template, status} — histogram (bucketed)
- http_requests_in_flight — gauge
- db_query_duration_seconds — histogram (optional, populated by SQLAlchemy event listener)
- app_info{version} — constant info gauge

Thread-safety: a threading.Lock guards mutations. Prometheus scraping happens
infrequently (every 15s) so the lock contention is negligible.
"""
import logging
import os
import threading
import time
from collections import defaultdict
from typing import Optional

logger = logging.getLogger("guineecare.metrics")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_lock = threading.Lock()

# Counters: {(method, path_template, status): int}
_request_counts: dict[tuple[str, str, str], int] = defaultdict(int)

# Histograms: {(method, path_template, status): {bucket_le: count, "sum": float, "count": int}}
# Buckets in seconds (Prometheus convention — le = "less than or equal")
_HISTOGRAM_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_request_duration: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
    lambda: {**{f"le={b}": 0 for b in _HISTOGRAM_BUCKETS}, "le=+Inf": 0, "sum": 0.0, "count": 0}
)

# Gauge: in-flight requests
_in_flight: int = 0

# App info (set once at startup)
_app_info: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_app_info(version: str, environment: str = "unknown") -> None:
    """Set the static app_info gauge labels (called once at startup)."""
    with _lock:
        _app_info["version"] = version
        _app_info["environment"] = environment


def observe_request_start() -> None:
    global _in_flight
    with _lock:
        _in_flight += 1


def observe_request_end(
    method: str,
    path_template: str,
    status: int,
    duration_seconds: float,
) -> None:
    """Record one completed HTTP request."""
    global _in_flight
    key = (method, path_template, str(status))
    with _lock:
        _in_flight -= 1
        _request_counts[key] += 1
        hist = _request_duration[key]
        hist["sum"] += duration_seconds
        hist["count"] += 1
        hist["le=+Inf"] += 1
        for bucket in _HISTOGRAM_BUCKETS:
            if duration_seconds <= bucket:
                hist[f"le={bucket}"] += 1


def render_prometheus() -> str:
    """Render all metrics in Prometheus text exposition format (version 0.0.4)."""
    lines: list[str] = []

    with _lock:
        # --- app_info ---
        if _app_info:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(_app_info.items()))
            lines.append("# HELP app_info GuinéeCare application info (constant).")
            lines.append("# TYPE app_info gauge")
            lines.append(f"app_info{{{label_str}}} 1")
            lines.append("")

        # --- http_requests_total ---
        lines.append("# HELP http_requests_total Total HTTP requests by method/path/status.")
        lines.append("# TYPE http_requests_total counter")
        for (method, path, status), count in sorted(_request_counts.items()):
            lines.append(
                f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
            )
        lines.append("")

        # --- http_request_duration_seconds ---
        lines.append("# HELP http_request_duration_seconds HTTP request latency in seconds.")
        lines.append("# TYPE http_request_duration_seconds histogram")
        for (method, path, status), hist in sorted(_request_duration.items()):
            label_base = f'method="{method}",path="{path}",status="{status}"'
            for bucket in _HISTOGRAM_BUCKETS:
                lines.append(
                    f'http_request_duration_seconds_bucket{{{label_base},le="{bucket}"}} {hist[f"le={bucket}"]}'
                )
            lines.append(
                f'http_request_duration_seconds_bucket{{{label_base},le="+Inf"}} {hist["le=+Inf"]}'
            )
            lines.append(f'http_request_duration_seconds_sum{{{label_base}}} {hist["sum"]}')
            lines.append(f'http_request_duration_seconds_count{{{label_base}}} {hist["count"]}')
        lines.append("")

        # --- http_requests_in_flight ---
        lines.append("# HELP http_requests_in_flight Current in-flight HTTP requests.")
        lines.append("# TYPE http_requests_in_flight gauge")
        lines.append(f"http_requests_in_flight {_in_flight}")
        lines.append("")

    return "\n".join(lines)
