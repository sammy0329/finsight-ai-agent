"""T-507: get_financials_tool 테스트 -- Supabase 재무지표 조회."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

from unittest.mock import MagicMock, patch  # noqa: E402

from app.core.config import settings  # noqa: E402

SAMPLE_METRICS_ROW = {
    "ticker": "005930",
    "period": "2025Q1",
    "per": 12.3,
    "pbr": 1.1,
    "roe": 0.082,
    "eps": 3500.0,
    "revenue": 320_000_000_000_000,
    "op_income": 45_000_000_000_000,
    "net_income": 35_000_000_000_000,
}

_SUPABASE_URL = "https://test.supabase.co"
_SUPABASE_KEY = "test-service-role-key"


class TestGetFinancials:
    """get_financials 함수 단위 테스트."""

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_returns_formatted_metrics(self, mock_create_client):
        """정상 응답 시 포맷팅된 재무지표 문자열을 반환한다."""
        from app.agent.tools import get_financials

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_METRICS_ROW
        ]

        result = get_financials("005930")

        assert "005930" in result
        assert "2025Q1" in result
        assert "PER" in result
        assert "PBR" in result
        assert "ROE" in result

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_formats_per_pbr_correctly(self, mock_create_client):
        """PER, PBR이 올바르게 포맷팅된다."""
        from app.agent.tools import get_financials

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_METRICS_ROW
        ]

        result = get_financials("005930")

        assert "12.30" in result or "12.3" in result
        assert "1.10" in result or "1.1" in result

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_formats_roe_as_percentage(self, mock_create_client):
        """ROE가 퍼센트 형식으로 표시된다."""
        from app.agent.tools import get_financials

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            SAMPLE_METRICS_ROW
        ]

        result = get_financials("005930")

        assert "8.2%" in result

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_returns_no_data_message_when_empty(self, mock_create_client):
        """데이터 없을 시 안내 메시지를 반환한다."""
        from app.agent.tools import get_financials

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        result = get_financials("999999")

        assert "없" in result or "데이터" in result

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_handles_exception_gracefully(self, mock_create_client):
        """예외 발생 시 오류 메시지를 반환한다."""
        from app.agent.tools import get_financials

        mock_create_client.side_effect = Exception("Connection error")

        result = get_financials("005930")

        assert "오류" in result

    @patch.object(settings, "supabase_url", _SUPABASE_URL)
    @patch.object(settings, "supabase_service_role_key", _SUPABASE_KEY)
    @patch("supabase.create_client")
    def test_handles_none_values(self, mock_create_client):
        """일부 값이 None일 때 N/A로 처리된다."""
        from app.agent.tools import get_financials

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "ticker": "005930",
                "period": "2025Q1",
                "per": None,
                "pbr": None,
                "roe": None,
                "eps": None,
                "revenue": None,
                "op_income": None,
            }
        ]

        result = get_financials("005930")

        assert "N/A" in result

    @patch.object(settings, "supabase_url", "")
    @patch.object(settings, "supabase_service_role_key", "")
    def test_returns_config_error_when_supabase_not_set(self):
        """Supabase 설정이 없을 때 안내 메시지를 반환한다."""
        from app.agent.tools import get_financials

        result = get_financials("005930")

        assert "설정" in result or "없" in result
