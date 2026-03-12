"""T-602/T-605: Supabase upsert 확장 모듈 테스트 (daily_prices, market_indices, fx_rates)."""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# TestUpsertDailyPrices
# ---------------------------------------------------------------------------
class TestUpsertDailyPrices:
    """upsert_daily_prices() 테스트."""

    SAMPLE_PRICES = [
        {
            "ticker": "005930",
            "date": "2026-03-12",
            "open": 70000,
            "high": 72000,
            "low": 69000,
            "close": 71000,
            "volume": 1000000,
        }
    ]

    @patch("app.pipeline.supabase_store.create_client")
    def test_normal_upsert(self, mock_create_client):
        """정상 upsert: 삽입 건수 반환."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = self.SAMPLE_PRICES
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_daily_prices

        count = upsert_daily_prices("http://url", "key", self.SAMPLE_PRICES)

        assert count == 1
        mock_client.table.assert_called_once_with("daily_prices")
        mock_client.table.return_value.upsert.assert_called_once_with(
            self.SAMPLE_PRICES, on_conflict="ticker,date"
        )

    @patch("app.pipeline.supabase_store.create_client")
    def test_multiple_records(self, mock_create_client):
        """여러 건 upsert."""
        records = self.SAMPLE_PRICES * 5
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = records
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_daily_prices

        count = upsert_daily_prices("http://url", "key", records)
        assert count == 5

    def test_empty_list_returns_zero(self):
        """빈 리스트 입력 시 0 반환."""
        from app.pipeline.supabase_store import upsert_daily_prices

        count = upsert_daily_prices("http://url", "key", [])
        assert count == 0

    @patch("app.pipeline.supabase_store.create_client")
    def test_exception_returns_zero(self, mock_create_client):
        """예외 발생 시 0 반환."""
        mock_create_client.side_effect = Exception("connection failed")

        from app.pipeline.supabase_store import upsert_daily_prices

        count = upsert_daily_prices("http://url", "key", self.SAMPLE_PRICES)
        assert count == 0


# ---------------------------------------------------------------------------
# TestUpsertMarketIndices
# ---------------------------------------------------------------------------
class TestUpsertMarketIndices:
    """upsert_market_indices() 테스트."""

    SAMPLE_INDICES = [
        {
            "symbol": "KS11",
            "name": "KOSPI",
            "date": "2026-03-12",
            "close": 2612.34,
            "change_pct": 0.80,
            "market": "KOR",
        }
    ]

    @patch("app.pipeline.supabase_store.create_client")
    def test_normal_upsert(self, mock_create_client):
        """정상 upsert: 삽입 건수 반환."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = self.SAMPLE_INDICES
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_market_indices

        count = upsert_market_indices("http://url", "key", self.SAMPLE_INDICES)

        assert count == 1
        mock_client.table.assert_called_once_with("market_indices")
        mock_client.table.return_value.upsert.assert_called_once_with(
            self.SAMPLE_INDICES, on_conflict="symbol,date"
        )

    def test_empty_list_returns_zero(self):
        """빈 리스트 입력 시 0 반환."""
        from app.pipeline.supabase_store import upsert_market_indices

        count = upsert_market_indices("http://url", "key", [])
        assert count == 0

    @patch("app.pipeline.supabase_store.create_client")
    def test_exception_returns_zero(self, mock_create_client):
        """예외 발생 시 0 반환."""
        mock_create_client.side_effect = RuntimeError("DB error")

        from app.pipeline.supabase_store import upsert_market_indices

        count = upsert_market_indices("http://url", "key", self.SAMPLE_INDICES)
        assert count == 0


# ---------------------------------------------------------------------------
# TestUpsertFxRates
# ---------------------------------------------------------------------------
class TestUpsertFxRates:
    """upsert_fx_rates() 테스트."""

    SAMPLE_RATES = [
        {
            "pair": "USD/KRW",
            "date": "2026-03-12",
            "rate": 1325.50,
        }
    ]

    @patch("app.pipeline.supabase_store.create_client")
    def test_normal_upsert(self, mock_create_client):
        """정상 upsert: 삽입 건수 반환."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.data = self.SAMPLE_RATES
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        from app.pipeline.supabase_store import upsert_fx_rates

        count = upsert_fx_rates("http://url", "key", self.SAMPLE_RATES)

        assert count == 1
        mock_client.table.assert_called_once_with("fx_rates")
        mock_client.table.return_value.upsert.assert_called_once_with(
            self.SAMPLE_RATES, on_conflict="pair,date"
        )

    def test_empty_list_returns_zero(self):
        """빈 리스트 입력 시 0 반환."""
        from app.pipeline.supabase_store import upsert_fx_rates

        count = upsert_fx_rates("http://url", "key", [])
        assert count == 0

    @patch("app.pipeline.supabase_store.create_client")
    def test_exception_returns_zero(self, mock_create_client):
        """예외 발생 시 0 반환."""
        mock_create_client.side_effect = RuntimeError("DB error")

        from app.pipeline.supabase_store import upsert_fx_rates

        count = upsert_fx_rates("http://url", "key", self.SAMPLE_RATES)
        assert count == 0
