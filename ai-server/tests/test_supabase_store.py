"""RED phase: Supabase upsert 모듈 테스트 (T-505)."""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# TestUpsertFinancialMetrics
# ---------------------------------------------------------------------------
class TestUpsertFinancialMetrics:
    """upsert_financial_metrics() 테스트."""

    SAMPLE_METRICS = [
        {
            "ticker": "005930",
            "period": "2025Q1",
            "per": 12.5,
            "pbr": 1.8,
            "roe": 0.15,
            "eps": 5000,
            "revenue": 300_000_000_000,
            "op_income": 50_000_000_000,
            "net_income": 40_000_000_000,
        }
    ]

    @patch("app.pipeline.supabase_store.create_client")
    def test_normal_upsert(self, mock_create_client):
        """정상 upsert: 삽입 건수 반환."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = self.SAMPLE_METRICS
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_financial_metrics

        count = upsert_financial_metrics("http://url", "key", self.SAMPLE_METRICS)

        assert count == 1
        mock_client.table.assert_called_once_with("financial_metrics")
        mock_client.table.return_value.upsert.assert_called_once_with(
            self.SAMPLE_METRICS, on_conflict="ticker,period"
        )

    @patch("app.pipeline.supabase_store.create_client")
    def test_multiple_records(self, mock_create_client):
        """여러 건 upsert."""
        records = self.SAMPLE_METRICS * 3
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = records
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_financial_metrics

        count = upsert_financial_metrics("http://url", "key", records)
        assert count == 3

    def test_empty_list_returns_zero(self):
        """빈 리스트 입력 시 0 반환, create_client 호출하지 않음."""
        from app.pipeline.supabase_store import upsert_financial_metrics

        count = upsert_financial_metrics("http://url", "key", [])
        assert count == 0

    @patch("app.pipeline.supabase_store.create_client")
    def test_exception_returns_zero(self, mock_create_client):
        """예외 발생 시 0 반환."""
        mock_create_client.side_effect = Exception("connection failed")

        from app.pipeline.supabase_store import upsert_financial_metrics

        count = upsert_financial_metrics("http://url", "key", self.SAMPLE_METRICS)
        assert count == 0


# ---------------------------------------------------------------------------
# TestUpsertCompanyProfiles
# ---------------------------------------------------------------------------
class TestUpsertCompanyProfiles:
    """upsert_company_profiles() 테스트."""

    SAMPLE_PROFILES = [
        {
            "ticker": "005930",
            "name": "Samsung Electronics",
            "market": "KOR",
            "sector": "Technology",
            "industry": "Semiconductors",
            "description": "Global tech company.",
        }
    ]

    @patch("app.pipeline.supabase_store.create_client")
    def test_normal_upsert(self, mock_create_client):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = self.SAMPLE_PROFILES
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_company_profiles

        count = upsert_company_profiles("http://url", "key", self.SAMPLE_PROFILES)

        assert count == 1
        mock_client.table.assert_called_once_with("company_profiles")
        mock_client.table.return_value.upsert.assert_called_once_with(
            self.SAMPLE_PROFILES, on_conflict="ticker"
        )

    def test_empty_list_returns_zero(self):
        from app.pipeline.supabase_store import upsert_company_profiles

        count = upsert_company_profiles("http://url", "key", [])
        assert count == 0

    @patch("app.pipeline.supabase_store.create_client")
    def test_exception_returns_zero(self, mock_create_client):
        mock_create_client.side_effect = RuntimeError("DB error")

        from app.pipeline.supabase_store import upsert_company_profiles

        count = upsert_company_profiles("http://url", "key", self.SAMPLE_PROFILES)
        assert count == 0
