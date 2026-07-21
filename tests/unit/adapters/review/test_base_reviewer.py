"""Tests for BaseReviewer and review models."""

from __future__ import annotations

from loopengine.adapters.outbound.review.base_reviewer import (
    BaseReviewer,
    IssueSeverity,
    ReviewIssue,
    ReviewReport,
)
from loopengine.core.ports.outbound.reviewer_port import ReviewVerdict


class ConcreteReviewer(BaseReviewer):
    @property
    def name(self) -> str:
        return "test-reviewer"


class TestIssueSeverity:
    def test_levels(self) -> None:
        assert IssueSeverity.CRITICAL == "critical"
        assert IssueSeverity.HIGH == "high"
        assert IssueSeverity.MEDIUM == "medium"
        assert IssueSeverity.LOW == "low"
        assert IssueSeverity.INFO == "info"


class TestReviewIssue:
    def test_defaults(self) -> None:
        issue = ReviewIssue(message="test")
        assert issue.message == "test"
        assert issue.severity == IssueSeverity.MEDIUM
        assert issue.file == ""
        assert issue.line == 0
        assert issue.category == ""
        assert issue.recommendation == ""
        assert issue.rule == ""


class TestReviewReport:
    def test_counts(self) -> None:
        issues = [
            ReviewIssue(message="c", severity=IssueSeverity.CRITICAL),
            ReviewIssue(message="h", severity=IssueSeverity.HIGH),
            ReviewIssue(message="h2", severity=IssueSeverity.HIGH),
            ReviewIssue(message="m", severity=IssueSeverity.MEDIUM),
            ReviewIssue(message="l", severity=IssueSeverity.LOW),
        ]
        report = ReviewReport(reviewer="test", score=5.0, issues=issues)
        assert report.critical_count == 1
        assert report.high_count == 2
        assert report.medium_count == 1
        assert report.low_count == 1

    def test_empty_report(self) -> None:
        report = ReviewReport(reviewer="test")
        assert report.critical_count == 0
        assert report.score == 0.0
        assert report.issues == []


class TestBaseReviewer:
    def test_name(self) -> None:
        r = ConcreteReviewer()
        assert r.name == "test-reviewer"

    def test_review_with_no_issues(self) -> None:
        r = ConcreteReviewer()
        result = r.review(goal="test", artifacts=[])
        assert result.verdict == ReviewVerdict.APPROVED
        assert result.score == 10.0
        assert result.comments == []
        assert result.metadata["reviewer"] == "test-reviewer"

    def test_score_calculation_critical(self) -> None:
        r = ConcreteReviewer()
        issues = [ReviewIssue(message="c", severity=IssueSeverity.CRITICAL)]
        score = r._calculate_score(issues)
        assert score == 7.0

    def test_score_calculation_high(self) -> None:
        r = ConcreteReviewer()
        issues = [ReviewIssue(message="h", severity=IssueSeverity.HIGH)]
        score = r._calculate_score(issues)
        assert score == 8.0

    def test_score_calculation_medium(self) -> None:
        r = ConcreteReviewer()
        issues = [ReviewIssue(message="m", severity=IssueSeverity.MEDIUM)]
        score = r._calculate_score(issues)
        assert score == 9.0

    def test_score_calculation_low(self) -> None:
        r = ConcreteReviewer()
        issues = [ReviewIssue(message="l", severity=IssueSeverity.LOW)]
        score = r._calculate_score(issues)
        assert score == 9.5

    def test_score_floors_at_zero(self) -> None:
        r = ConcreteReviewer()
        issues = [ReviewIssue(message="c", severity=IssueSeverity.CRITICAL)] * 10
        score = r._calculate_score(issues)
        assert score == 0.0

    def test_score_ceils_at_ten(self) -> None:
        r = ConcreteReviewer()
        score = r._calculate_score([])
        assert score == 10.0

    def test_verdict_approved(self) -> None:
        r = ConcreteReviewer()
        assert r._score_to_verdict(10.0) == ReviewVerdict.APPROVED
        assert r._score_to_verdict(8.0) == ReviewVerdict.APPROVED

    def test_verdict_changes_requested(self) -> None:
        r = ConcreteReviewer()
        assert r._score_to_verdict(7.0) == ReviewVerdict.CHANGES_REQUESTED
        assert r._score_to_verdict(5.0) == ReviewVerdict.CHANGES_REQUESTED

    def test_verdict_rejected(self) -> None:
        r = ConcreteReviewer()
        assert r._score_to_verdict(4.0) == ReviewVerdict.REJECTED
        assert r._score_to_verdict(0.0) == ReviewVerdict.REJECTED

    def test_generate_summary_no_issues(self) -> None:
        r = ConcreteReviewer()
        summary = r._generate_summary(10.0, [])
        assert "No issues found" in summary

    def test_generate_summary_with_issues(self) -> None:
        r = ConcreteReviewer()
        issues = [
            ReviewIssue(message="a", severity=IssueSeverity.HIGH),
            ReviewIssue(message="b", severity=IssueSeverity.HIGH),
            ReviewIssue(message="c", severity=IssueSeverity.LOW),
        ]
        summary = r._generate_summary(7.0, issues)
        assert "7.0" in summary
        assert "2 high" in summary
        assert "1 low" in summary

    def test_get_content(self) -> None:
        artifacts = [
            {"kind": "file", "path": "a.py", "content": "hello"},
            {"kind": "other", "content": "world"},
        ]
        assert BaseReviewer._get_content(artifacts, "other") == "world"
        assert BaseReviewer._get_content(artifacts, "missing") == ""

    def test_get_files(self) -> None:
        artifacts = [
            {"kind": "file", "path": "a.py", "content": "hello"},
            {"kind": "file", "path": "b.py", "content": "world"},
            {"kind": "other", "content": "ignored"},
        ]
        files = BaseReviewer._get_files(artifacts)
        assert files == {"a.py": "hello", "b.py": "world"}

    def test_count_lines(self) -> None:
        files = {"a.py": "line1\nline2\nline3", "b.py": "one"}
        assert BaseReviewer._count_lines(files) == 4

    def test_has_pattern(self) -> None:
        files = {"a.py": "def foo():\n    pass\ndef bar():\n    pass"}
        matches = BaseReviewer._has_pattern(files, r"def (\w+)")
        assert len(matches) == 2
        assert matches[0] == ("a.py", 1)
        assert matches[1] == ("a.py", 3)
