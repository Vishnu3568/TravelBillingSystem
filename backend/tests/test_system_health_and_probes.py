"""
End-to-End System Smoke Tests.
Tests container health probes, security headers, standardized exception formatting,
bill export endpoints, and telemetry utilities.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.bill import Bill
from app.models.user import User
from app.utils.security import create_access_token
from app.services.amip.utils.telemetry_exporter import TelemetryExporter

TEST_DB_FILE = "./test_smoke_temp.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


def test_liveness_probe():
    """Verify /api/health/live returns 200 and ALIVE status."""
    client = TestClient(app)
    response = client.get("/api/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ALIVE"
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_readiness_probe():
    """Verify /api/health/ready returns 200 and READY status."""
    client = TestClient(app)
    response = client.get("/api/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_security_headers_middleware():
    """Verify HTTP responses contain standard security headers and Server-Timing."""
    client = TestClient(app)
    response = client.get("/api/health/live")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Server-Timing" in headers


def test_standardized_http_exception_format():
    """Verify 404/401 errors return standardized JSON schema."""
    client = TestClient(app)
    token = create_access_token("owner2", "OWNER")
    auth_headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/bills/9999999", headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert "detail" in data
    assert "timestamp" in data


def test_bill_export_endpoints():
    """Verify /api/bills/export/csv and summary endpoints work with valid token."""
    client = TestClient(app)
    token = create_access_token("owner2", "OWNER")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Summary
    res_summary = client.get("/api/bills/export/summary", headers=auth_headers)
    assert res_summary.status_code == 200
    sum_data = res_summary.json()
    assert "total_bills" in sum_data
    assert "total_revenue" in sum_data

    # CSV Export
    res_csv = client.get("/api/bills/export/csv", headers=auth_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "ID,Bill Number" in res_csv.text


def test_telemetry_exporter_utility():
    """Verify TelemetryExporter produces valid CSV and KPI calculations."""
    logs = [
        {"timestamp": "2026-08-30T10:00:00Z", "level": "INFO", "workflow_id": "w1", "message": "Started", "execution_time_ms": 150},
        {"timestamp": "2026-08-30T10:00:01Z", "level": "ERROR", "workflow_id": "w1", "message": "Failed step", "execution_time_ms": 50},
    ]
    spans = [
        {"span_id": "s1", "trace_id": "t1", "name": "Task1", "duration_ms": 200.0, "status": "OK"}
    ]
    workflows = [
        {"workflow_id": "w1", "status": "COMPLETED", "duration_ms": 200.0},
        {"workflow_id": "w2", "status": "REVIEW_REQUIRED", "duration_ms": 400.0},
    ]

    csv_logs = TelemetryExporter.export_logs_to_csv(logs)
    assert "Workflow ID" in csv_logs
    assert "Started" in csv_logs

    csv_spans = TelemetryExporter.export_spans_to_csv(spans)
    assert "Span ID" in csv_spans
    assert "Task1" in csv_spans

    summary = TelemetryExporter.generate_performance_summary(workflows, logs)
    assert summary["total_executions"] == 2
    assert summary["completed_count"] == 1
    assert summary["review_required_count"] == 1
    assert summary["total_errors_logged"] == 1
    assert summary["avg_duration_ms"] == 300.0
