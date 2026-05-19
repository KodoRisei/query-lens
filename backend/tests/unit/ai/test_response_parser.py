import json

from app.ai.base import LLMResponse
from app.ai.response_parser import AIResponseParser
from app.domain.models.analysis import (
    AnalysisFinding,
    FindingCategory,
    Severity,
    StaticAnalysisResult,
)

parser = AIResponseParser()


def make_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=100,
        output_tokens=200,
    )


def empty_analysis() -> StaticAnalysisResult:
    return StaticAnalysisResult()


def analysis_with_finding() -> StaticAnalysisResult:
    return StaticAnalysisResult(
        findings=[
            AnalysisFinding(
                rule_id="select_star",
                severity=Severity.warning,
                category=FindingCategory.performance,
                title="SELECT * detected",
                message="Fetches all columns.",
            )
        ]
    )


def test_parses_bare_json():
    payload = {
        "summary": "Two issues found.",
        "improved_query": "SELECT id FROM users",
        "findings": [
            {
                "rule_id": "select_star",
                "explanation": "SELECT * is inefficient.",
                "suggestion": "List specific columns.",
            }
        ],
        "educational_note": None,
    }
    review = parser.parse(make_response(json.dumps(payload)), empty_analysis())
    assert review.summary == "Two issues found."
    assert review.improved_query == "SELECT id FROM users"
    assert len(review.findings) == 1
    assert review.findings[0].rule_id == "select_star"


def test_parses_json_in_code_fence():
    payload = {
        "summary": "All good.",
        "findings": [],
        "improved_query": None,
        "educational_note": None,
    }
    content = f"```json\n{json.dumps(payload)}\n```"
    review = parser.parse(make_response(content), empty_analysis())
    assert review.summary == "All good."


def test_fallback_on_plain_text():
    review = parser.parse(make_response("This query looks fine to me."), empty_analysis())
    assert "This query looks fine" in review.summary
    assert review.findings == []


def test_fallback_on_malformed_json():
    review = parser.parse(make_response("{not valid json}"), empty_analysis())
    assert "{not valid json}" in review.summary


def test_empty_findings_with_static_fallback():
    # When LLM returns no findings but static analysis has them,
    # the parser should synthesize findings from the static result.
    payload = {
        "summary": "Reviewed.",
        "findings": [],
        "improved_query": None,
        "educational_note": None,
    }
    review = parser.parse(make_response(json.dumps(payload)), analysis_with_finding())
    assert len(review.findings) == 1
    assert review.findings[0].rule_id == "select_star"


def test_educational_note_preserved():
    payload = {
        "summary": "Here is what I found.",
        "findings": [],
        "improved_query": None,
        "educational_note": "Indexes speed up lookups by keeping data sorted.",
    }
    review = parser.parse(make_response(json.dumps(payload)), empty_analysis())
    assert review.educational_note == "Indexes speed up lookups by keeping data sorted."


def test_tokens_carried_through():
    payload = {"summary": "ok", "findings": [], "improved_query": None, "educational_note": None}
    review = parser.parse(make_response(json.dumps(payload)), empty_analysis())
    assert review.input_tokens == 100
    assert review.output_tokens == 200
    assert review.provider == "openai"


def test_findings_without_suggestion_allowed():
    payload = {
        "summary": "One issue.",
        "findings": [{"rule_id": "x", "explanation": "Something bad.", "suggestion": None}],
        "improved_query": None,
        "educational_note": None,
    }
    review = parser.parse(make_response(json.dumps(payload)), empty_analysis())
    assert review.findings[0].suggestion is None
