"""T-202: API 요청/응답 Pydantic 스키마 검증 테스트."""

import pytest
from pydantic import ValidationError

from app.api.schemas import InsightRequest, InsightResponse


# ================================================================== #
# InsightRequest
# ================================================================== #
class TestInsightRequest:
    """InsightRequest 스키마 검증 테스트."""

    def test_valid_segment_a(self):
        """user_segment 'A'로 유효한 요청을 생성할 수 있다."""
        req = InsightRequest(user_segment="A", query="삼성전자 실적 분석")
        assert req.user_segment == "A"
        assert req.query == "삼성전자 실적 분석"

    def test_valid_segment_b(self):
        """user_segment 'B'로 유효한 요청을 생성할 수 있다."""
        req = InsightRequest(user_segment="B", query="반도체 시장 전망")
        assert req.user_segment == "B"

    def test_valid_segment_c(self):
        """user_segment 'C'로 유효한 요청을 생성할 수 있다."""
        req = InsightRequest(user_segment="C", query="코스피 분석")
        assert req.user_segment == "C"

    def test_invalid_segment_rejected(self):
        """user_segment가 A/B/C가 아니면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightRequest(user_segment="D", query="테스트")

    def test_empty_segment_rejected(self):
        """user_segment가 빈 문자열이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightRequest(user_segment="", query="테스트")

    def test_missing_query_rejected(self):
        """query가 누락되면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightRequest(user_segment="A")

    def test_missing_segment_rejected(self):
        """user_segment가 누락되면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightRequest(query="테스트")

    def test_lowercase_segment_rejected(self):
        """소문자 세그먼트는 거부된다."""
        with pytest.raises(ValidationError):
            InsightRequest(user_segment="a", query="테스트")


# ================================================================== #
# InsightResponse
# ================================================================== #
class TestInsightResponse:
    """InsightResponse 스키마 검증 테스트."""

    def test_valid_response(self):
        """유효한 응답을 생성할 수 있다."""
        resp = InsightResponse(insight="인사이트 내용", sources=["source1", "source2"])
        assert resp.insight == "인사이트 내용"
        assert resp.sources == ["source1", "source2"]

    def test_empty_sources_allowed(self):
        """sources가 빈 리스트여도 허용된다."""
        resp = InsightResponse(insight="인사이트", sources=[])
        assert resp.sources == []

    def test_missing_insight_rejected(self):
        """insight가 누락되면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightResponse(sources=["src"])

    def test_missing_sources_rejected(self):
        """sources가 누락되면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightResponse(insight="인사이트")

    def test_sources_must_be_list_of_strings(self):
        """sources가 문자열 리스트가 아니면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            InsightResponse(insight="test", sources=[1, 2])
