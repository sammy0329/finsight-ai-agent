"""T-603/T-604: 지수/환율 수집 모듈 테스트."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd

from app.pipeline.market_collector import fetch_fx_rates, fetch_market_indices


# ---------------------------------------------------------------------------
# TestFetchMarketIndices
# ---------------------------------------------------------------------------
class TestFetchMarketIndices:
    """fetch_market_indices() 테스트."""

    @patch("app.pipeline.market_collector.fdr")
    def test_returns_kor_indices(self, mock_fdr):
        """KOR 시장 지수(KOSPI, KOSDAQ)를 올바른 형식으로 반환한다."""
        mock_df = pd.DataFrame(
            {"Close": [2612.34], "Change": [0.008]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_market_indices("2026-03-12", market="KOR")

        assert len(result) == 2
        symbols = {r["symbol"] for r in result}
        assert symbols == {"KS11", "KQ11"}

        row = result[0]
        assert row["date"] == "2026-03-12"
        assert row["close"] == 2612.34
        assert isinstance(row["change_pct"], float)
        assert row["market"] == "KOR"
        assert "name" in row

    @patch("app.pipeline.market_collector.fdr")
    def test_returns_us_indices(self, mock_fdr):
        """US 시장 지수(S&P500, NASDAQ, DOW)를 올바른 형식으로 반환한다."""
        mock_df = pd.DataFrame(
            {"Close": [5200.50], "Change": [0.012]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_market_indices("2026-03-12", market="US")

        assert len(result) == 3
        symbols = {r["symbol"] for r in result}
        assert symbols == {"GSPC", "IXIC", "DJI"}

        for row in result:
            assert row["market"] == "US"
            assert row["date"] == "2026-03-12"

    @patch("app.pipeline.market_collector.fdr")
    def test_returns_empty_on_exception(self, mock_fdr):
        """fdr 예외 발생 시 빈 리스트를 반환한다."""
        mock_fdr.DataReader.side_effect = Exception("Network error")

        result = fetch_market_indices("2026-03-12", market="KOR")

        assert result == []

    @patch("app.pipeline.market_collector.fdr")
    def test_skips_empty_dataframe(self, mock_fdr):
        """빈 DataFrame 반환 시 해당 지수를 건너뛴다."""
        mock_fdr.DataReader.return_value = pd.DataFrame()

        result = fetch_market_indices("2026-03-12", market="KOR")

        assert result == []

    @patch("app.pipeline.market_collector.fdr")
    def test_skips_failed_symbol_continues_others(self, mock_fdr):
        """한 심볼 실패해도 나머지 심볼은 정상 수집한다."""
        mock_df = pd.DataFrame(
            {"Close": [2612.34], "Change": [0.008]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )

        def side_effect(symbol, start, end):
            if symbol == "KS11":
                raise Exception("API error")
            return mock_df

        mock_fdr.DataReader.side_effect = side_effect

        result = fetch_market_indices("2026-03-12", market="KOR")

        assert len(result) == 1
        assert result[0]["symbol"] == "KQ11"

    @patch("app.pipeline.market_collector.fdr")
    def test_change_pct_calculation(self, mock_fdr):
        """Change 값을 퍼센트로 변환한다 (0.008 -> 0.80)."""
        mock_df = pd.DataFrame(
            {"Close": [2612.34], "Change": [0.008]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_market_indices("2026-03-12", market="KOR")

        assert result[0]["change_pct"] == 0.80

    @patch("app.pipeline.market_collector.fdr")
    def test_field_types(self, mock_fdr):
        """반환 dict의 필드 타입이 올바르다."""
        mock_df = pd.DataFrame(
            {"Close": [2612.34], "Change": [0.008]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_market_indices("2026-03-12", market="KOR")

        row = result[0]
        assert isinstance(row["symbol"], str)
        assert isinstance(row["name"], str)
        assert isinstance(row["date"], str)
        assert isinstance(row["close"], float)
        assert isinstance(row["change_pct"], float)
        assert isinstance(row["market"], str)


# ---------------------------------------------------------------------------
# TestFetchFxRates
# ---------------------------------------------------------------------------
class TestFetchFxRates:
    """fetch_fx_rates() 테스트."""

    @patch("app.pipeline.market_collector.fdr")
    def test_returns_fx_rates(self, mock_fdr):
        """USD/KRW, EUR/KRW 환율을 올바른 형식으로 반환한다."""
        mock_df = pd.DataFrame(
            {"Close": [1325.50]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_fx_rates("2026-03-12")

        assert len(result) == 2
        pairs = {r["pair"] for r in result}
        assert pairs == {"USD/KRW", "EUR/KRW"}

        row = result[0]
        assert row["date"] == "2026-03-12"
        assert row["rate"] == 1325.50

    @patch("app.pipeline.market_collector.fdr")
    def test_returns_empty_on_exception(self, mock_fdr):
        """fdr 예외 발생 시 빈 리스트를 반환한다."""
        mock_fdr.DataReader.side_effect = Exception("Network error")

        result = fetch_fx_rates("2026-03-12")

        assert result == []

    @patch("app.pipeline.market_collector.fdr")
    def test_skips_empty_dataframe(self, mock_fdr):
        """빈 DataFrame 반환 시 해당 환율을 건너뛴다."""
        mock_fdr.DataReader.return_value = pd.DataFrame()

        result = fetch_fx_rates("2026-03-12")

        assert result == []

    @patch("app.pipeline.market_collector.fdr")
    def test_skips_failed_pair_continues_others(self, mock_fdr):
        """한 환율 쌍 실패해도 나머지는 정상 수집한다."""
        mock_df = pd.DataFrame(
            {"Close": [1450.00]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )

        def side_effect(pair, start, end):
            if pair == "USD/KRW":
                raise Exception("API error")
            return mock_df

        mock_fdr.DataReader.side_effect = side_effect

        result = fetch_fx_rates("2026-03-12")

        assert len(result) == 1
        assert result[0]["pair"] == "EUR/KRW"

    @patch("app.pipeline.market_collector.fdr")
    def test_field_types(self, mock_fdr):
        """반환 dict의 필드 타입이 올바르다."""
        mock_df = pd.DataFrame(
            {"Close": [1325.50]},
            index=pd.DatetimeIndex([datetime(2026, 3, 12)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_fx_rates("2026-03-12")

        row = result[0]
        assert isinstance(row["pair"], str)
        assert isinstance(row["date"], str)
        assert isinstance(row["rate"], float)
