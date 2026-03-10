"""T-108: 데이터 정제 공통 모듈 테스트."""

from app.pipeline.cleaner import (
    clean_news_items,
    deduplicate,
    filter_empty,
    remove_html_tags,
)


# ================================================================== #
# remove_html_tags
# ================================================================== #
class TestRemoveHtmlTags:
    """HTML 태그 및 엔티티 제거 테스트."""

    def test_removes_simple_tags(self):
        """<b>, <br> 등 단순 태그를 제거한다."""
        assert remove_html_tags("<b>강조</b> 텍스트") == "강조 텍스트"

    def test_removes_nested_tags(self):
        """중첩된 태그도 모두 제거한다."""
        html = "<div><p>안녕<span>하세요</span></p></div>"
        assert remove_html_tags(html) == "안녕하세요"

    def test_removes_html_entities(self):
        """&amp; &lt; &gt; &quot; 등 HTML 엔티티를 변환한다."""
        assert remove_html_tags("A &amp; B &lt; C &gt; D") == "A & B < C > D"

    def test_removes_numeric_entities(self):
        """&#39; 등 숫자형 엔티티도 변환한다."""
        assert remove_html_tags("it&#39;s fine") == "it's fine"

    def test_empty_string(self):
        """빈 문자열을 입력하면 빈 문자열을 반환한다."""
        assert remove_html_tags("") == ""

    def test_plain_text_unchanged(self):
        """태그 없는 텍스트는 그대로 반환한다."""
        assert remove_html_tags("일반 텍스트") == "일반 텍스트"

    def test_self_closing_tags(self):
        """<br/>, <img/> 등 셀프 클로징 태그도 제거한다."""
        assert remove_html_tags("줄바꿈<br/>여기") == "줄바꿈여기"

    def test_tag_with_attributes(self):
        """속성이 있는 태그도 제거한다."""
        html = '<a href="http://example.com">링크</a>'
        assert remove_html_tags(html) == "링크"


# ================================================================== #
# deduplicate
# ================================================================== #
class TestDeduplicate:
    """key 필드 기준 중복 제거 테스트."""

    def test_removes_duplicate_items(self):
        """같은 key 값을 가진 항목 중 첫 번째만 유지한다."""
        items = [
            {"link": "a", "title": "first"},
            {"link": "b", "title": "second"},
            {"link": "a", "title": "duplicate"},
        ]
        result = deduplicate(items, "link")
        assert len(result) == 2
        assert result[0]["title"] == "first"
        assert result[1]["title"] == "second"

    def test_empty_list(self):
        """빈 리스트를 입력하면 빈 리스트를 반환한다."""
        assert deduplicate([], "link") == []

    def test_no_duplicates(self):
        """중복이 없으면 원본과 동일한 길이를 반환한다."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = deduplicate(items, "id")
        assert len(result) == 3

    def test_all_duplicates(self):
        """모두 같은 key면 하나만 남긴다."""
        items = [{"k": "x", "v": 1}, {"k": "x", "v": 2}, {"k": "x", "v": 3}]
        result = deduplicate(items, "k")
        assert len(result) == 1
        assert result[0]["v"] == 1

    def test_missing_key_field(self):
        """key 필드가 없는 항목은 별도로 취급한다(None 키로 처리)."""
        items = [
            {"link": "a", "title": "A"},
            {"title": "no link"},
            {"link": "a", "title": "dup"},
        ]
        result = deduplicate(items, "link")
        # "a" 하나 + None 키 하나
        assert len(result) == 2

    def test_preserves_order(self):
        """중복 제거 후에도 원래 순서를 유지한다."""
        items = [{"k": "c"}, {"k": "a"}, {"k": "b"}, {"k": "a"}]
        result = deduplicate(items, "k")
        assert [r["k"] for r in result] == ["c", "a", "b"]


# ================================================================== #
# filter_empty
# ================================================================== #
class TestFilterEmpty:
    """필수 필드 빈값 필터 테스트."""

    def test_removes_items_with_empty_required_field(self):
        """required_fields 중 하나라도 빈 문자열이면 제거한다."""
        items = [
            {"title": "ok", "link": "http://a"},
            {"title": "", "link": "http://b"},
            {"title": "ok2", "link": ""},
        ]
        result = filter_empty(items, ["title", "link"])
        assert len(result) == 1
        assert result[0]["title"] == "ok"

    def test_removes_items_with_none_required_field(self):
        """None 값도 빈값으로 취급한다."""
        items = [{"title": None, "link": "http://a"}]
        result = filter_empty(items, ["title"])
        assert len(result) == 0

    def test_removes_items_with_missing_required_field(self):
        """required_fields에 해당하는 키 자체가 없으면 제거한다."""
        items = [{"link": "http://a"}]
        result = filter_empty(items, ["title", "link"])
        assert len(result) == 0

    def test_empty_list(self):
        """빈 리스트를 입력하면 빈 리스트를 반환한다."""
        assert filter_empty([], ["title"]) == []

    def test_no_required_fields(self):
        """required_fields가 빈 리스트면 모든 항목을 유지한다."""
        items = [{"a": ""}, {"b": None}]
        result = filter_empty(items, [])
        assert len(result) == 2

    def test_whitespace_only_treated_as_empty(self):
        """공백만 있는 문자열도 빈값으로 취급한다."""
        items = [{"title": "   ", "link": "http://a"}]
        result = filter_empty(items, ["title"])
        assert len(result) == 0


# ================================================================== #
# clean_news_items
# ================================================================== #
class TestCleanNewsItems:
    """뉴스 리스트 전체 정제 통합 테스트."""

    def test_full_pipeline(self):
        """HTML 제거 -> 중복 제거(link) -> 빈값 필터(title, link) 순으로 처리한다."""
        items = [
            {"title": "<b>뉴스1</b>", "link": "http://a", "desc": "내용"},
            {"title": "<b>뉴스2</b>", "link": "http://b", "desc": "내용2"},
            {"title": "<b>중복뉴스</b>", "link": "http://a", "desc": "중복"},
            {"title": "", "link": "http://c", "desc": "제목없음"},
        ]
        result = clean_news_items(items)

        assert len(result) == 2
        assert result[0]["title"] == "뉴스1"
        assert result[1]["title"] == "뉴스2"

    def test_empty_list(self):
        """빈 리스트를 입력하면 빈 리스트를 반환한다."""
        assert clean_news_items([]) == []

    def test_all_invalid_items(self):
        """모든 항목이 필터링되면 빈 리스트를 반환한다."""
        items = [
            {"title": "", "link": ""},
            {"title": "", "link": "http://a"},
        ]
        result = clean_news_items(items)
        assert result == []

    def test_html_entities_cleaned(self):
        """HTML 엔티티도 정제한 후 필터링한다."""
        items = [{"title": "A &amp; B", "link": "http://a"}]
        result = clean_news_items(items)
        assert result[0]["title"] == "A & B"

    def test_preserves_extra_fields(self):
        """title, link 외의 필드도 유지한다."""
        items = [{"title": "ok", "link": "http://a", "pubDate": "2025-03-10"}]
        result = clean_news_items(items)
        assert result[0]["pubDate"] == "2025-03-10"
