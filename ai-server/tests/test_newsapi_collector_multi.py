"""T-122: fetch_us_news_multi 함수 테스트."""

from unittest.mock import patch

from app.pipeline.newsapi_collector import fetch_us_news_multi


class TestFetchUsNewsMulti:
    """fetch_us_news_multi 함수 테스트 스위트."""

    QUERIES = [
        {"category": "macro", "query": "Federal Reserve interest rate", "page_size": 15},
        {"category": "big_tech", "query": "Apple Google Microsoft", "page_size": 10},
    ]

    SAMPLE_ARTICLES = [
        {
            "title": "Fed holds rates",
            "description": "The Federal Reserve kept rates steady.",
            "publishedAt": "2025-03-10T12:00:00Z",
            "url": "https://example.com/fed",
        },
    ]

    # ------------------------------------------------------------------ #
    # 정상 동작
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_returns_combined_results(self, mock_fetch, mock_sleep):
        """여러 쿼리의 결과를 합쳐서 반환한다."""
        mock_fetch.return_value = self.SAMPLE_ARTICLES

        result = fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_attaches_category_to_each_item(self, mock_fetch, mock_sleep):
        """각 기사에 해당 쿼리의 category가 부착된다."""
        mock_fetch.side_effect = [
            [
                {
                    "title": "Fed news",
                    "description": "Content",
                    "publishedAt": "2025",
                    "url": "http://a.com",
                }
            ],
            [
                {
                    "title": "Tech news",
                    "description": "Content",
                    "publishedAt": "2025",
                    "url": "http://b.com",
                }
            ],
        ]

        result = fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        assert result[0]["category"] == "macro"
        assert result[1]["category"] == "big_tech"

    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_calls_fetch_for_each_query(self, mock_fetch, mock_sleep):
        """각 쿼리마다 fetch_us_news가 호출된다."""
        mock_fetch.return_value = []

        fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        assert mock_fetch.call_count == 2

    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_passes_page_size_to_fetch(self, mock_fetch, mock_sleep):
        """page_size가 fetch_us_news에 전달된다."""
        mock_fetch.return_value = []

        fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        first_call = mock_fetch.call_args_list[0]
        second_call = mock_fetch.call_args_list[1]

        # page_size가 keyword arg로 전달됨
        if first_call.kwargs:
            assert first_call.kwargs.get("page_size") == 15
            assert second_call.kwargs.get("page_size") == 10
        else:
            # positional: api_key, query, date, page_size
            assert first_call[0][3] == 15
            assert second_call[0][3] == 10

    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_sleeps_between_queries(self, mock_fetch, mock_sleep):
        """쿼리 사이에 sleep(1.0)이 호출된다."""
        mock_fetch.return_value = []

        fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        assert mock_sleep.call_count >= 1
        mock_sleep.assert_called_with(1.0)

    # ------------------------------------------------------------------ #
    # 빈 입력
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_empty_queries_returns_empty(self, mock_fetch, mock_sleep):
        """빈 쿼리 리스트를 넣으면 빈 리스트를 반환한다."""
        result = fetch_us_news_multi([], "api_key", "2025-03-10")

        assert result == []
        mock_fetch.assert_not_called()

    # ------------------------------------------------------------------ #
    # 부분 실패
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_partial_failure_returns_other_results(self, mock_fetch, mock_sleep):
        """한 쿼리가 빈 결과를 반환해도 다른 쿼리 결과는 포함된다."""
        mock_fetch.side_effect = [
            [],
            [
                {
                    "title": "Apple earnings",
                    "description": "Content",
                    "publishedAt": "2025",
                    "url": "http://a.com",
                }
            ],
        ]

        result = fetch_us_news_multi(self.QUERIES, "api_key", "2025-03-10")

        assert len(result) == 1
        assert result[0]["category"] == "big_tech"

    # ------------------------------------------------------------------ #
    # API 키 전달
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.newsapi_collector.fetch_us_news")
    def test_passes_api_key_correctly(self, mock_fetch, mock_sleep):
        """api_key가 올바르게 전달된다."""
        mock_fetch.return_value = []
        queries = [{"category": "test", "query": "test", "page_size": 10}]

        fetch_us_news_multi(queries, "my_api_key", "2025-03-10")

        call_kwargs = mock_fetch.call_args
        if call_kwargs.kwargs:
            assert call_kwargs.kwargs["api_key"] == "my_api_key"
        else:
            assert call_kwargs[0][0] == "my_api_key"
