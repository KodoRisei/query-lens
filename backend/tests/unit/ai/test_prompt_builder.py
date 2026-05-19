import pytest

from app.ai.prompts.builder import PromptBuilder
from app.domain.models.analysis import AnalysisFinding, FindingCategory, Severity, StaticAnalysisResult
from app.domain.models.query import ReviewMode, SQLQuery

builder = PromptBuilder()


def make_query(sql: str, mode: ReviewMode = ReviewMode.senior) -> SQLQuery:
    return SQLQuery(sql=sql, review_mode=mode)


def make_result(findings: list[AnalysisFinding] | None = None) -> StaticAnalysisResult:
    return StaticAnalysisResult(findings=findings or [])


def test_messages_have_system_and_user():
    messages = builder.build_review_messages(make_query("SELECT 1"), make_result())
    roles = [m.role for m in messages]
    assert roles == ["system", "user"]


def test_sql_appears_in_user_message():
    sql = "SELECT id FROM users WHERE active = true"
    messages = builder.build_review_messages(make_query(sql), make_result())
    assert sql in messages[1].content


def test_junior_system_prompt_is_encouraging():
    messages = builder.build_review_messages(
        make_query("SELECT 1", mode=ReviewMode.junior), make_result()
    )
    system = messages[0].content.lower()
    assert any(word in system for word in ["junior", "mentor", "learning", "encouraging"])


def test_senior_system_prompt_is_direct():
    messages = builder.build_review_messages(
        make_query("SELECT 1", mode=ReviewMode.senior), make_result()
    )
    system = messages[0].content.lower()
    assert any(word in system for word in ["senior", "direct", "technical"])


def test_performance_system_prompt_is_focused():
    messages = builder.build_review_messages(
        make_query("SELECT 1", mode=ReviewMode.performance), make_result()
    )
    system = messages[0].content.lower()
    assert "performance" in system


def test_findings_appear_in_user_message():
    finding = AnalysisFinding(
        rule_id="select_star",
        severity=Severity.warning,
        category=FindingCategory.performance,
        title="SELECT * detected",
        message="This fetches all columns.",
        suggestion="List only needed columns.",
    )
    messages = builder.build_review_messages(make_query("SELECT *"), make_result([finding]))
    user = messages[1].content
    assert "select_star" in user
    assert "SELECT * detected" in user


def test_no_findings_message_present():
    messages = builder.build_review_messages(make_query("SELECT 1"), make_result())
    assert "No anti-patterns" in messages[1].content


def test_response_schema_included():
    messages = builder.build_review_messages(make_query("SELECT 1"), make_result())
    assert '"summary"' in messages[1].content
    assert '"improved_query"' in messages[1].content
    assert '"findings"' in messages[1].content
