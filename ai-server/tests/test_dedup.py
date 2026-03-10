"""T-123: 중복 제거 모듈 테스트."""

from app.pipeline.dedup import deduplicate_by_url


class TestDeduplicateByUrl:
    """deduplicate_by_url 함수 테스트 스위트."""

    def test_removes_duplicate_urls(self):
        """같은 URL을 가진 항목은 중복 제거된다."""
        items = [
            {"title": "뉴스1", "link": "http://a.com"},
            {"title": "뉴스2", "link": "http://b.com"},
            {"title": "뉴스1 복사", "link": "http://a.com"},
        ]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 2

    def test_keeps_first_occurrence(self):
        """중복 시 먼저 나온 항목이 유지된다."""
        items = [
            {"title": "첫번째", "link": "http://a.com"},
            {"title": "두번째", "link": "http://a.com"},
        ]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 1
        assert result[0]["title"] == "첫번째"

    def test_no_duplicates_returns_all(self):
        """중복이 없으면 모든 항목을 반환한다."""
        items = [
            {"title": "뉴스1", "link": "http://a.com"},
            {"title": "뉴스2", "link": "http://b.com"},
            {"title": "뉴스3", "link": "http://c.com"},
        ]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 3

    def test_empty_list_returns_empty(self):
        """빈 리스트를 넣으면 빈 리스트를 반환한다."""
        result = deduplicate_by_url([], "link")
        assert result == []

    def test_single_item(self):
        """단일 항목 리스트는 그대로 반환한다."""
        items = [{"title": "뉴스", "link": "http://a.com"}]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 1

    def test_uses_correct_key_field(self):
        """지정된 key_field를 기준으로 중복을 판단한다."""
        items = [
            {"title": "뉴스1", "url": "http://a.com", "link": "http://x.com"},
            {"title": "뉴스2", "url": "http://a.com", "link": "http://y.com"},
        ]
        # url 기준 중복 제거
        result = deduplicate_by_url(items, "url")
        assert len(result) == 1

        # link 기준으로는 중복 아님
        result = deduplicate_by_url(items, "link")
        assert len(result) == 2

    def test_missing_key_field_treated_as_none(self):
        """key_field가 없는 항목은 None으로 취급되어 하나만 남는다."""
        items = [
            {"title": "뉴스1"},
            {"title": "뉴스2"},
        ]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 1

    def test_preserves_order(self):
        """원본 순서가 유지된다."""
        items = [
            {"title": "A", "link": "http://a.com"},
            {"title": "B", "link": "http://b.com"},
            {"title": "C", "link": "http://c.com"},
            {"title": "A copy", "link": "http://a.com"},
        ]
        result = deduplicate_by_url(items, "link")
        titles = [r["title"] for r in result]
        assert titles == ["A", "B", "C"]

    def test_large_list_performance(self):
        """대량 데이터에서도 정상 동작한다."""
        items = [{"title": f"뉴스{i}", "link": f"http://{i % 500}.com"} for i in range(10000)]
        result = deduplicate_by_url(items, "link")
        assert len(result) == 500
