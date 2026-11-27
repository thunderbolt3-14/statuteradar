import json
from pathlib import Path

from statuteradar.analysis.assessment import assess_case
from statuteradar.api import AssessmentRequestInput, create_app


ROOT = Path(__file__).resolve().parents[1]


def test_api_request_model_runs_through_shared_assessment_engine():
    payload = json.loads((ROOT / "examples" / "phase5" / "synthetic_conflict.json").read_text(encoding="utf-8"))
    request = AssessmentRequestInput.model_validate(payload)

    result = assess_case(request.to_core())

    assert result.label == "CONFLICT"
    assert result.case_id == "synthetic-conflict-001"
    assert result.requires_human_review is True


def test_api_exposes_versioned_assessment_and_health_routes():
    app = create_app()
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    assert ("/health", "GET") in routes
    assert ("/api/v1/assess", "POST") in routes
