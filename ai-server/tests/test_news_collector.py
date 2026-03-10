"""T-106: Naver Search API 뉴스 수집 모듈 테스트."""

from unittest.mock import MagicMock, patch

from app.pipeline.news_collector import fetch_naver_news


class TestFetchNaverNews:
    """fetch_naver_news 함수 테스트 스위트."""

    SAMPLE_RESPONSE = {
        "lastBuildDate": "Mon, 10 Mar 2025 10:00:00 +0900",
        "total": 2,
        "start": 1,
        "display": 2,
        "items": [
            {
                "title": "삼성전자 <b>실적</b> 발표",
                "originallink": "https://example.com/1",
                "link": "https://n.news.naver.com/1",
                "description": "삼성전자가 2025년 1분기 실적을 발표했다.",
                "pubDate": "Mon, 10 Mar 2025 09:00:00 +0900",
            },
            {
                "title": "SK하이닉스 <b>HBM</b> 수주",
                "originallink": "https://example.com/2",
                "link": "https://n.news.naver.com/2",
                "description": "SK하이닉스가 HBM 대규모 수주 계약을 체결했다.",
                "pubDate": "Mon, 10 Mar 2025 08:00:00 +0900",
            },
        ],
    }

    # ------------------------------------------------------------------ #
    # 정상 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.news_collector.requests.get")
    def test_returns_news_list(self, mock_get):
        """정상 응답 시 뉴스 dict 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_naver_news("client_id", "client_secret", "삼성전자", "20250310")

        assert isinstance(result, list)
        assert len(result) == 2
        assert "title" in result[0]
        assert "description" in result[0]
        assert "pubDate" in result[0]
        assert "link" in result[0]

    @patch("app.pipeline.news_collector.requests.get")
    def test_strips_html_tags_from_title(self, mock_get):
        """title에서 HTML 태그가 제거된다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_naver_news("cid", "csec", "삼성전자", "20250310")

        assert "<b>" not in result[0]["title"]
        assert "</b>" not in result[0]["title"]

    @patch("app.pipeline.news_collector.requests.get")
    def test_passes_correct_headers_and_params(self, mock_get):
        """API 요청에 올바른 헤더와 파라미터가 전달된다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": []}
        mock_get.return_value = mock_resp

        fetch_naver_news("my_id", "my_secret", "주식", "20250310")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert headers["X-Naver-Client-Id"] == "my_id"
        assert headers["X-Naver-Client-Secret"] == "my_secret"
        assert params["query"] == "주식"

    @patch("app.pipeline.news_collector.requests.get")
    def test_strips_html_tags_from_description(self, mock_get):
        """description에서도 HTML 태그가 제거된다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {
                    "title": "test",
                    "description": "<b>강조</b> 내용 &quot;인용&quot;",
                    "pubDate": "Mon, 10 Mar 2025 09:00:00 +0900",
                    "link": "https://example.com",
                }
            ]
        }
        mock_get.return_value = mock_resp

        result = fetch_naver_news("cid", "csec", "테스트", "20250310")

        assert "<b>" not in result[0]["description"]

    # ------------------------------------------------------------------ #
    # 빈 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.news_collector.requests.get")
    def test_returns_empty_list_when_no_items(self, mock_get):
        """items가 빈 배열이면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": []}
        mock_get.return_value = mock_resp

        result = fetch_naver_news("cid", "csec", "없는뉴스", "20250310")

        assert result == []

    @patch("app.pipeline.news_collector.requests.get")
    def test_returns_empty_list_when_items_key_missing(self, mock_get):
        """응답에 items 키가 없으면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp

        result = fetch_naver_news("cid", "csec", "test", "20250310")

        assert result == []

    # ------------------------------------------------------------------ #
    # API 오류 / 예외 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.news_collector.requests.get")
    def test_returns_empty_list_on_http_error(self, mock_get):
        """HTTP 오류 시 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.raise_for_status.side_effect = Exception("Rate limited")
        mock_get.return_value = mock_resp

        result = fetch_naver_news("cid", "csec", "test", "20250310")

        assert result == []

    @patch("app.pipeline.news_collector.requests.get")
    def test_returns_empty_list_on_network_error(self, mock_get):
        """네트워크 예외 발생 시 빈 리스트를 반환한다."""
        mock_get.side_effect = ConnectionError("DNS resolution failed")

        result = fetch_naver_news("cid", "csec", "test", "20250310")

        assert result == []
