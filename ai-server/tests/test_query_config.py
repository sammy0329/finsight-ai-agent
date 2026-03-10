"""T-121: 쿼리 설정 구조 검증 테스트."""


class TestKorQueries:
    """KOR_QUERIES 구조 검증."""

    def test_kor_queries_is_list(self):
        """KOR_QUERIES는 리스트이다."""
        from app.pipeline.query_config import KOR_QUERIES

        assert isinstance(KOR_QUERIES, list)

    def test_kor_queries_not_empty(self):
        """KOR_QUERIES는 비어있지 않다."""
        from app.pipeline.query_config import KOR_QUERIES

        assert len(KOR_QUERIES) > 0

    def test_kor_queries_have_required_keys(self):
        """각 항목에 category, query 키가 존재한다."""
        from app.pipeline.query_config import KOR_QUERIES

        for item in KOR_QUERIES:
            assert "category" in item, f"Missing 'category' in {item}"
            assert "query" in item, f"Missing 'query' in {item}"

    def test_kor_queries_values_are_strings(self):
        """category와 query 값은 문자열이다."""
        from app.pipeline.query_config import KOR_QUERIES

        for item in KOR_QUERIES:
            assert isinstance(item["category"], str)
            assert isinstance(item["query"], str)

    def test_kor_queries_categories_are_unique(self):
        """KOR_QUERIES의 category는 중복이 없다."""
        from app.pipeline.query_config import KOR_QUERIES

        categories = [q["category"] for q in KOR_QUERIES]
        assert len(categories) == len(set(categories))

    def test_kor_queries_contains_expected_categories(self):
        """KOR_QUERIES에 주요 카테고리가 포함되어 있다."""
        from app.pipeline.query_config import KOR_QUERIES

        categories = {q["category"] for q in KOR_QUERIES}
        expected = {"macro", "stock_market", "semiconductor", "exchange_rate", "energy"}
        assert expected.issubset(categories)

    def test_kor_queries_no_page_size(self):
        """KOR_QUERIES 항목에는 page_size 키가 없다."""
        from app.pipeline.query_config import KOR_QUERIES

        for item in KOR_QUERIES:
            assert "page_size" not in item

    def test_kor_queries_query_not_empty(self):
        """각 query 문자열은 비어있지 않다."""
        from app.pipeline.query_config import KOR_QUERIES

        for item in KOR_QUERIES:
            assert len(item["query"].strip()) > 0


class TestUsQueries:
    """US_QUERIES 구조 검증."""

    def test_us_queries_is_list(self):
        """US_QUERIES는 리스트이다."""
        from app.pipeline.query_config import US_QUERIES

        assert isinstance(US_QUERIES, list)

    def test_us_queries_not_empty(self):
        """US_QUERIES는 비어있지 않다."""
        from app.pipeline.query_config import US_QUERIES

        assert len(US_QUERIES) > 0

    def test_us_queries_have_required_keys(self):
        """각 항목에 category, query, page_size 키가 존재한다."""
        from app.pipeline.query_config import US_QUERIES

        for item in US_QUERIES:
            assert "category" in item, f"Missing 'category' in {item}"
            assert "query" in item, f"Missing 'query' in {item}"
            assert "page_size" in item, f"Missing 'page_size' in {item}"

    def test_us_queries_page_size_is_positive_int(self):
        """page_size는 양의 정수이다."""
        from app.pipeline.query_config import US_QUERIES

        for item in US_QUERIES:
            assert isinstance(item["page_size"], int)
            assert item["page_size"] > 0

    def test_us_queries_categories_are_unique(self):
        """US_QUERIES의 category는 중복이 없다."""
        from app.pipeline.query_config import US_QUERIES

        categories = [q["category"] for q in US_QUERIES]
        assert len(categories) == len(set(categories))

    def test_us_queries_contains_expected_categories(self):
        """US_QUERIES에 주요 카테고리가 포함되어 있다."""
        from app.pipeline.query_config import US_QUERIES

        categories = {q["category"] for q in US_QUERIES}
        expected = {"macro", "stock_market", "semiconductor", "energy", "big_tech", "crypto"}
        assert expected.issubset(categories)

    def test_us_queries_query_is_english(self):
        """US_QUERIES의 query는 영어 문자열이다."""
        from app.pipeline.query_config import US_QUERIES

        for item in US_QUERIES:
            assert isinstance(item["query"], str)
            assert len(item["query"].strip()) > 0
