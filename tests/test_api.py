import json
from dataclasses import asdict
from pathlib import Path

from fastapi.testclient import TestClient

from statuteradar.analysis.assessment import assess_case
from statuteradar.api import AssessmentRequestInput, AssessmentResponse, create_app


ROOT = Path(__file__).resolve().parents[1]


def test_api_request_model_runs_through_shared_assessment_engine():
    payload = json.loads(
        (ROOT / "examples" / "phase5" / "synthetic_conflict.json").read_text(
            encoding="utf-8"
        )
    )
    request = AssessmentRequestInput.model_validate(payload)

    result = assess_case(request.to_core())

    assert result.label == "CONFLICT"
    assert result.case_id == "synthetic-conflict-001"
    assert result.requires_human_review is True
    response = AssessmentResponse.model_validate(asdict(result))
    assert {item.rule_id for item in response.evidence} == {
        "fictional-rule-a",
        "fictional-rule-b",
    }
    assert response.evidence[0].source_chunk_id == "synthetic:a:1"
    assert response.scope_evidence is not None
    assert response.scope_evidence.reviewed_by == "synthetic-fixture"


def test_api_exposes_versioned_assessment_and_health_routes():
    app = create_app()
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    assert ("/health", "GET") in routes
    assert ("/api/v1/assess", "POST") in routes


def test_http_assessment_returns_reviewed_evidence():
    payload = json.loads(
        (ROOT / "examples" / "phase5" / "synthetic_conflict.json").read_text(
            encoding="utf-8"
        )
    )

    with TestClient(create_app()) as client:
        response = client.post("/api/v1/assess", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert result["label"] == "CONFLICT"
    assert {item["rule_id"] for item in result["evidence"]} == {
        "fictional-rule-a",
        "fictional-rule-b",
    }
    assert result["scope_evidence"]["reviewed_by"] == "synthetic-fixture"
