"""T-107: NewsAPI 미국 뉴스 수집 모듈 테스트."""

from unittest.mock import MagicMock, patch

from app.pipeline.newsapi_collector import fetch_us_news


class TestFetchUsNews:
    """fetch_us_news 함수 테스트 스위트."""

    SAMPLE_RESPONSE = {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "title": "NVIDIA earnings beat expectations",
                "description": "NVIDIA reported Q4 earnings that exceeded analyst expectations.",
                "publishedAt": "2025-03-10T14:00:00Z",
                "url": "https://example.com/nvidia",
                "source": {"id": "reuters", "name": "Reuters"},
                "author": "John Doe",
            },
            {
                "title": "Fed holds rates steady",
                "description": "The Federal Reserve kept interest rates unchanged.",
                "publishedAt": "2025-03-10T12:00:00Z",
                "url": "https://example.com/fed",
                "source": {"id": "ap", "name": "AP"},
                "author": "Jane Smith",
            },
        ],
    }

    # ------------------------------------------------------------------ #
    # 정상 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_news_list(self, mock_get):
        """정상 응답 시 뉴스 dict 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_us_news("test_api_key", "NVIDIA", "2025-03-10")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "NVIDIA earnings beat expectations"
        assert result[0]["description"] is not None
        assert result[0]["publishedAt"] == "2025-03-10T14:00:00Z"
        assert result[0]["url"] == "https://example.com/nvidia"

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_passes_correct_params_to_api(self, mock_get):
        """API에 올바른 파라미터가 전달된다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
        mock_get.return_value = mock_resp

        fetch_us_news("my_key", "Apple", "2025-03-10")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["apiKey"] == "my_key"
        assert params["q"] == "Apple"
        assert "2025-03-10" in params.get("from", "")

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_only_required_fields(self, mock_get):
        """반환 dict에 title, description, publishedAt, url 필드가 존재한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_us_news("key", "test", "2025-03-10")

        required_keys = {"title", "description", "publishedAt", "url"}
        for item in result:
            assert required_keys.issubset(item.keys())

    # ------------------------------------------------------------------ #
    # 빈 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_empty_list_when_no_articles(self, mock_get):
        """articles가 빈 배열이면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
        mock_get.return_value = mock_resp

        result = fetch_us_news("key", "nonexistent", "2025-03-10")

        assert result == []

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_empty_list_when_articles_key_missing(self, mock_get):
        """응답에 articles 키가 없으면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_resp

        result = fetch_us_news("key", "test", "2025-03-10")

        assert result == []

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_filters_out_removed_articles(self, mock_get):
        """[Removed] 제목의 기사는 필터링한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "title": "[Removed]",
                    "description": "[Removed]",
                    "publishedAt": "2025-03-10T10:00:00Z",
                    "url": "https://removed.com",
                },
                {
                    "title": "Valid article",
                    "description": "Content",
                    "publishedAt": "2025-03-10T10:00:00Z",
                    "url": "https://example.com",
                },
            ],
        }
        mock_get.return_value = mock_resp

        result = fetch_us_news("key", "test", "2025-03-10")

        assert len(result) == 1
        assert result[0]["title"] == "Valid article"

    # ------------------------------------------------------------------ #
    # API 오류 / 예외 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_empty_list_on_api_error_status(self, mock_get):
        """API가 error status를 반환하면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "Your API key is invalid.",
        }
        mock_get.return_value = mock_resp

        result = fetch_us_news("bad_key", "test", "2025-03-10")

        assert result == []

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_empty_list_on_http_error(self, mock_get):
        """HTTP 오류 시 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = Exception("Unauthorized")
        mock_get.return_value = mock_resp

        result = fetch_us_news("key", "test", "2025-03-10")

        assert result == []

    @patch("app.pipeline.newsapi_collector.requests.get")
    def test_returns_empty_list_on_network_error(self, mock_get):
        """네트워크 예외 발생 시 빈 리스트를 반환한다."""
        mock_get.side_effect = ConnectionError("Timeout")

        result = fetch_us_news("key", "test", "2025-03-10")

        assert result == []
