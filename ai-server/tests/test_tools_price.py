"""T-222: get_price_tool 테스트 -- Yahoo Finance 가격 조회."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

SAMPLE_YAHOO_RESPONSE = {
    "chart": {
        "result": [
            {
                "meta": {
                    "currency": "KRW",
                    "symbol": "005930.KS",
                    "regularMarketPrice": 71000,
                    "previousClose": 70000,
                    "chartPreviousClose": 70000,
                },
                "indicators": {
                    "quote": [
                        {
                            "close": [69000, 70000, 71000],
                            "open": [68500, 69500, 70500],
                            "high": [69500, 70500, 71500],
                            "low": [68000, 69000, 70000],
                            "volume": [1000000, 1200000, 1100000],
                        }
                    ]
                },
            }
        ],
        "error": None,
    }
}


class TestGetPrice:
    """get_price 함수 단위 테스트."""

    @patch("app.agent.tools.httpx.get")
    def test_returns_formatted_price(self, mock_get):
        """정상 응답 시 포맷팅된 가격 정보를 반환한다."""
        from app.agent.tools import get_price

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_YAHOO_RESPONSE
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_price("005930.KS")

        assert "71000" in result or "71,000" in result
        assert "005930" in result or "삼성" in result or "KS" in result

    @patch("app.agent.tools.httpx.get")
    def test_includes_change_rate(self, mock_get):
        """등락률 정보가 포함된다."""
        from app.agent.tools import get_price

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_YAHOO_RESPONSE
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_price("005930.KS")

        # 71000 vs 70000 = +1.43%
        assert "%" in result

    @patch("app.agent.tools.httpx.get")
    def test_handles_api_error_gracefully(self, mock_get):
        """API 오류 시 에러 메시지를 반환한다."""
        from app.agent.tools import get_price

        mock_get.side_effect = Exception("Network error")

        result = get_price("INVALID")

        assert "오류" in result or "실패" in result

    @patch("app.agent.tools.httpx.get")
    def test_handles_invalid_response_format(self, mock_get):
        """잘못된 응답 형식을 처리한다."""
        from app.agent.tools import get_price

        mock_response = MagicMock()
        mock_response.json.return_value = {"chart": {"result": None, "error": "Not found"}}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_price("INVALID_TICKER")

        assert "오류" in result or "찾을 수 없" in result

    @patch("app.agent.tools.httpx.get")
    def test_includes_currency_info(self, mock_get):
        """통화 정보가 포함된다."""
        from app.agent.tools import get_price

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_YAHOO_RESPONSE
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_price("005930.KS")

        assert "KRW" in result or "원" in result
