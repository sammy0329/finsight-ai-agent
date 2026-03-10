"""T-104: FinanceDataReader 국내 주가 수집 모듈 테스트."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd

from app.pipeline.stock_collector import fetch_stock_data


class TestFetchStockData:
    """fetch_stock_data 함수 테스트 스위트."""

    # ------------------------------------------------------------------ #
    # 정상 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.stock_collector.fdr")
    def test_returns_ohlcv_for_single_ticker(self, mock_fdr):
        """단일 종목에 대해 올바른 OHLCV dict 리스트를 반환한다."""
        mock_df = pd.DataFrame(
            {
                "Open": [70000],
                "High": [72000],
                "Low": [69000],
                "Close": [71000],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2025, 3, 10)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_stock_data(["005930"], "2025-03-10", "2025-03-10")

        assert isinstance(result, list)
        assert len(result) == 1
        row = result[0]
        assert row["ticker"] == "005930"
        assert row["date"] == "2025-03-10"
        assert row["open"] == 70000
        assert row["high"] == 72000
        assert row["low"] == 69000
        assert row["close"] == 71000
        assert row["volume"] == 1000000

    @patch("app.pipeline.stock_collector.fdr")
    def test_returns_multiple_tickers(self, mock_fdr):
        """복수 종목에 대해 모든 결과를 합쳐서 반환한다."""
        mock_df = pd.DataFrame(
            {
                "Open": [70000],
                "High": [72000],
                "Low": [69000],
                "Close": [71000],
                "Volume": [500000],
            },
            index=pd.DatetimeIndex([datetime(2025, 3, 10)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_stock_data(["005930", "000660"], "2025-03-10", "2025-03-10")

        assert len(result) == 2
        tickers = {r["ticker"] for r in result}
        assert tickers == {"005930", "000660"}

    @patch("app.pipeline.stock_collector.fdr")
    def test_returns_multiple_dates(self, mock_fdr):
        """여러 날짜 데이터가 있으면 각각 별도 dict로 반환한다."""
        mock_df = pd.DataFrame(
            {
                "Open": [70000, 71000],
                "High": [72000, 73000],
                "Low": [69000, 70000],
                "Close": [71000, 72000],
                "Volume": [1000000, 900000],
            },
            index=pd.DatetimeIndex([datetime(2025, 3, 10), datetime(2025, 3, 11)]),
        )
        mock_fdr.DataReader.return_value = mock_df

        result = fetch_stock_data(["005930"], "2025-03-10", "2025-03-11")

        assert len(result) == 2
        assert result[0]["date"] == "2025-03-10"
        assert result[1]["date"] == "2025-03-11"

    # ------------------------------------------------------------------ #
    # 빈 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.stock_collector.fdr")
    def test_returns_empty_list_when_no_data(self, mock_fdr):
        """데이터가 없으면 빈 리스트를 반환한다."""
        mock_fdr.DataReader.return_value = pd.DataFrame()

        result = fetch_stock_data(["999999"], "2025-03-10", "2025-03-10")

        assert result == []

    def test_returns_empty_list_for_empty_tickers(self):
        """빈 티커 리스트가 입력되면 빈 리스트를 반환한다."""
        result = fetch_stock_data([], "2025-03-10", "2025-03-10")

        assert result == []

    # ------------------------------------------------------------------ #
    # API 오류 / 예외 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.stock_collector.fdr")
    def test_returns_empty_list_on_exception(self, mock_fdr):
        """FinanceDataReader 예외 발생 시 빈 리스트를 반환한다."""
        mock_fdr.DataReader.side_effect = Exception("Network error")

        result = fetch_stock_data(["005930"], "2025-03-10", "2025-03-10")

        assert result == []

    @patch("app.pipeline.stock_collector.fdr")
    def test_skips_failed_ticker_and_continues(self, mock_fdr):
        """한 종목이 실패해도 나머지 종목은 정상 수집한다."""
        mock_df = pd.DataFrame(
            {
                "Open": [70000],
                "High": [72000],
                "Low": [69000],
                "Close": [71000],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2025, 3, 10)]),
        )

        def side_effect(ticker, start, end):
            if ticker == "FAIL":
                raise Exception("API error")
            return mock_df

        mock_fdr.DataReader.side_effect = side_effect

        result = fetch_stock_data(["FAIL", "005930"], "2025-03-10", "2025-03-10")

        assert len(result) == 1
        assert result[0]["ticker"] == "005930"

    # ------------------------------------------------------------------ #
    # 입력 유효성
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.stock_collector.fdr")
    def test_date_format_passed_to_fdr(self, mock_fdr):
        """start_date, end_date가 그대로 fdr.DataReader에 전달된다."""
        mock_fdr.DataReader.return_value = pd.DataFrame()

        fetch_stock_data(["005930"], "2025-01-01", "2025-03-10")

        mock_fdr.DataReader.assert_called_once_with("005930", "2025-01-01", "2025-03-10")
