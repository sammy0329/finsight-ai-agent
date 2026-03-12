"""T-221: get_dart_tool 테스트 -- DART API 공시 목록 조회."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

SAMPLE_DART_RESPONSE = {
    "status": "000",
    "message": "정상",
    "list": [
        {
            "corp_name": "삼성전자",
            "report_nm": "사업보고서 (2024.12)",
            "rcept_dt": "20250301",
            "flr_nm": "삼성전자",
        },
        {
            "corp_name": "삼성전자",
            "report_nm": "분기보고서 (2024.09)",
            "rcept_dt": "20250215",
            "flr_nm": "삼성전자",
        },
    ],
}


class TestGetDartFilings:
    """get_dart_filings 함수 단위 테스트."""

    @patch("app.agent.tools.httpx.get")
    def test_returns_formatted_filings(self, mock_get):
        """정상 응답 시 포맷팅된 공시 목록을 반환한다."""
        from app.agent.tools import get_dart_filings

        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_DART_RESPONSE
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_dart_filings("삼성전자")

        assert "사업보고서" in result
        assert "분기보고서" in result
        assert "20250301" in result or "2025-03-01" in result or "2025.03.01" in result

    @patch("app.agent.tools.httpx.get")
    def test_handles_api_error_gracefully(self, mock_get):
        """API 오류 시 에러 메시지를 반환한다."""
        from app.agent.tools import get_dart_filings

        mock_get.side_effect = Exception("Connection timeout")

        result = get_dart_filings("삼성전자")

        assert "오류" in result or "실패" in result

    @patch("app.agent.tools.httpx.get")
    def test_handles_empty_filings_list(self, mock_get):
        """빈 공시 목록을 처리한다."""
        from app.agent.tools import get_dart_filings

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "000",
            "message": "정상",
            "list": [],
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_dart_filings("미등록기업")

        assert "공시" in result
        assert "없" in result or "0건" in result

    @patch("app.agent.tools.httpx.get")
    def test_handles_dart_error_status(self, mock_get):
        """DART API 자체의 에러 status 코드를 처리한다."""
        from app.agent.tools import get_dart_filings

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "013",
            "message": "조회된 데이터가 없습니다.",
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_dart_filings("비상장기업")

        assert "없" in result or "오류" in result

    @patch("app.agent.tools.httpx.get")
    def test_passes_correct_api_params(self, mock_get):
        """올바른 API 파라미터가 전달된다."""
        from app.agent.tools import get_dart_filings

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "000",
            "message": "정상",
            "list": [],
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        get_dart_filings("삼성전자")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        url = call_args[0][0] if call_args[0] else call_args[1].get("url", "")
        assert "opendart.fss.or.kr" in url

    @patch("app.agent.tools.httpx.get")
    def test_limits_filing_count(self, mock_get):
        """공시 목록 개수가 적절히 제한된다 (최대 10개)."""
        from app.agent.tools import get_dart_filings

        many_filings = [
            {
                "corp_name": "삼성전자",
                "report_nm": f"보고서{i}",
                "rcept_dt": f"2025030{i % 10}",
                "flr_nm": "삼성전자",
            }
            for i in range(20)
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "000",
            "message": "정상",
            "list": many_filings,
        }
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_dart_filings("삼성전자")

        # 20개 중 최대 10개만 포함해야 한다
        assert result.count("보고서") <= 10
