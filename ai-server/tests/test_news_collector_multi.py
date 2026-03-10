"""T-122: fetch_naver_news_multi 함수 테스트."""

from unittest.mock import patch

from app.pipeline.news_collector import fetch_naver_news_multi


class TestFetchNaverNewsMulti:
    """fetch_naver_news_multi 함수 테스트 스위트."""

    QUERIES = [
        {"category": "macro", "query": "금리 통화정책"},
        {"category": "stock_market", "query": "코스피 코스닥"},
    ]

    SAMPLE_ITEMS = [
        {
            "title": "금리 인하 전망",
            "description": "한국은행이 금리 인하를 시사했다.",
            "pubDate": "Mon, 10 Mar 2025 09:00:00 +0900",
            "link": "https://n.news.naver.com/1",
        },
    ]

    # ------------------------------------------------------------------ #
    # 정상 동작
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_returns_combined_results(self, mock_fetch, mock_sleep):
        """여러 쿼리의 결과를 합쳐서 반환한다."""
        mock_fetch.return_value = self.SAMPLE_ITEMS

        result = fetch_naver_news_multi(self.QUERIES, "cid", "csec", "20250310")

        assert isinstance(result, list)
        # 2개 쿼리 x 1개 결과 = 2개
        assert len(result) == 2

    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_attaches_category_to_each_item(self, mock_fetch, mock_sleep):
        """각 기사에 해당 쿼리의 category가 부착된다."""
        mock_fetch.side_effect = [
            [
                {
                    "title": "금리 뉴스",
                    "description": "내용",
                    "pubDate": "2025",
                    "link": "http://a.com",
                }
            ],
            [
                {
                    "title": "증시 뉴스",
                    "description": "내용",
                    "pubDate": "2025",
                    "link": "http://b.com",
                }
            ],
        ]

        result = fetch_naver_news_multi(self.QUERIES, "cid", "csec", "20250310")

        assert result[0]["category"] == "macro"
        assert result[1]["category"] == "stock_market"

    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_calls_fetch_for_each_query(self, mock_fetch, mock_sleep):
        """각 쿼리마다 fetch_naver_news가 호출된다."""
        mock_fetch.return_value = []

        fetch_naver_news_multi(self.QUERIES, "cid", "csec", "20250310")

        assert mock_fetch.call_count == 2
        # 첫 번째 호출: query="금리 통화정책"
        first_call = mock_fetch.call_args_list[0]
        assert first_call.kwargs.get("query") or first_call[0][2] == "금리 통화정책"

    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_sleeps_between_queries(self, mock_fetch, mock_sleep):
        """쿼리 사이에 sleep이 호출된다."""
        mock_fetch.return_value = []

        fetch_naver_news_multi(self.QUERIES, "cid", "csec", "20250310")

        # 2개 쿼리 사이에 1번 sleep (첫 번째 쿼리 후)
        assert mock_sleep.call_count >= 1
        mock_sleep.assert_called_with(0.5)

    # ------------------------------------------------------------------ #
    # 빈 입력
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_empty_queries_returns_empty(self, mock_fetch, mock_sleep):
        """빈 쿼리 리스트를 넣으면 빈 리스트를 반환한다."""
        result = fetch_naver_news_multi([], "cid", "csec", "20250310")

        assert result == []
        mock_fetch.assert_not_called()

    # ------------------------------------------------------------------ #
    # 부분 실패
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_partial_failure_still_returns_other_results(self, mock_fetch, mock_sleep):
        """한 쿼리가 빈 결과를 반환해도 다른 쿼리 결과는 포함된다."""
        mock_fetch.side_effect = [
            [],  # macro 실패
            [
                {
                    "title": "코스피 상승",
                    "description": "내용",
                    "pubDate": "2025",
                    "link": "http://a.com",
                }
            ],  # stock_market 성공
        ]

        result = fetch_naver_news_multi(self.QUERIES, "cid", "csec", "20250310")

        assert len(result) == 1
        assert result[0]["category"] == "stock_market"

    # ------------------------------------------------------------------ #
    # 기존 함수 호환성
    # ------------------------------------------------------------------ #
    @patch("time.sleep")
    @patch("app.pipeline.news_collector.fetch_naver_news")
    def test_passes_credentials_correctly(self, mock_fetch, mock_sleep):
        """client_id와 client_secret이 올바르게 전달된다."""
        mock_fetch.return_value = []
        queries = [{"category": "test", "query": "테스트"}]

        fetch_naver_news_multi(queries, "my_id", "my_secret", "20250310")

        call_kwargs = mock_fetch.call_args
        # positional or keyword args
        if call_kwargs.kwargs:
            assert call_kwargs.kwargs["client_id"] == "my_id"
            assert call_kwargs.kwargs["client_secret"] == "my_secret"
        else:
            assert call_kwargs[0][0] == "my_id"
            assert call_kwargs[0][1] == "my_secret"
