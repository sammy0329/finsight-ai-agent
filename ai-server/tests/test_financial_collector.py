"""RED phase: 재무지표·기업개요 수집 모듈 테스트 (T-503, T-504)."""

from datetime import date
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# TestCurrentQuarter
# ---------------------------------------------------------------------------
class TestCurrentQuarter:
    """current_quarter() 유틸 함수 테스트."""

    def test_returns_string_format(self):
        from app.pipeline.financial_collector import current_quarter

        result = current_quarter()
        # "2026Q1" 형태
        assert isinstance(result, str)
        assert result[4] == "Q"
        assert len(result) == 6

    @patch("app.pipeline.financial_collector.date")
    def test_q1(self, mock_date):
        mock_date.today.return_value = date(2025, 2, 15)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        from app.pipeline.financial_collector import current_quarter

        assert current_quarter() == "2025Q1"

    @patch("app.pipeline.financial_collector.date")
    def test_q2(self, mock_date):
        mock_date.today.return_value = date(2025, 5, 1)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        from app.pipeline.financial_collector import current_quarter

        assert current_quarter() == "2025Q2"

    @patch("app.pipeline.financial_collector.date")
    def test_q3(self, mock_date):
        mock_date.today.return_value = date(2025, 9, 30)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        from app.pipeline.financial_collector import current_quarter

        assert current_quarter() == "2025Q3"

    @patch("app.pipeline.financial_collector.date")
    def test_q4(self, mock_date):
        mock_date.today.return_value = date(2025, 12, 31)
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
        from app.pipeline.financial_collector import current_quarter

        assert current_quarter() == "2025Q4"


# ---------------------------------------------------------------------------
# TestFetchFinancialMetrics
# ---------------------------------------------------------------------------
class TestFetchFinancialMetrics:
    """fetch_financial_metrics() 테스트."""

    SAMPLE_INFO = {
        "trailingPE": 12.5,
        "priceToBook": 1.8,
        "returnOnEquity": 0.15,
        "trailingEps": 5000,
        "totalRevenue": 300_000_000_000,
        "operatingIncome": 50_000_000_000,
        "netIncomeToCommon": 40_000_000_000,
    }

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_normal_kor(self, mock_ticker_cls):
        """KOR 종목은 ticker.KS 심볼로 호출한다."""
        mock_ticker = MagicMock()
        mock_ticker.info = self.SAMPLE_INFO
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("005930", market="KOR")

        mock_ticker_cls.assert_called_once_with("005930.KS")
        assert result is not None
        assert result["ticker"] == "005930"
        assert result["per"] == 12.5
        assert result["pbr"] == 1.8
        assert result["roe"] == 0.15
        assert result["eps"] == 5000
        assert result["revenue"] == 300_000_000_000
        assert result["op_income"] == 50_000_000_000
        assert result["net_income"] == 40_000_000_000
        assert "period" in result

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_normal_us(self, mock_ticker_cls):
        """US 종목은 ticker 그대로 호출한다."""
        mock_ticker = MagicMock()
        mock_ticker.info = self.SAMPLE_INFO
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("AAPL", market="US")

        mock_ticker_cls.assert_called_once_with("AAPL")
        assert result is not None
        assert result["ticker"] == "AAPL"

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_empty_info_returns_none(self, mock_ticker_cls):
        """info가 빈 dict이면 None 반환."""
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("005930")
        assert result is None

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_none_info_returns_none(self, mock_ticker_cls):
        """info가 None이면 None 반환."""
        mock_ticker = MagicMock()
        mock_ticker.info = None
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("005930")
        assert result is None

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_exception_returns_none(self, mock_ticker_cls):
        """yfinance 예외 발생 시 None 반환."""
        mock_ticker_cls.side_effect = Exception("network error")

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("005930")
        assert result is None

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_partial_info(self, mock_ticker_cls):
        """일부 필드만 존재해도 정상 반환 (None 필드 포함)."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"trailingPE": 10.0}
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_financial_metrics

        result = fetch_financial_metrics("MSFT", market="US")
        assert result is not None
        assert result["per"] == 10.0
        assert result["pbr"] is None
        assert result["roe"] is None


# ---------------------------------------------------------------------------
# TestFetchCompanyProfile
# ---------------------------------------------------------------------------
class TestFetchCompanyProfile:
    """fetch_company_profile() 테스트."""

    SAMPLE_INFO = {
        "longName": "Samsung Electronics Co., Ltd.",
        "shortName": "Samsung Electronics",
        "sector": "Technology",
        "industry": "Semiconductors",
        "longBusinessSummary": "Samsung is a global tech company.",
    }

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_normal(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = self.SAMPLE_INFO
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_company_profile

        result = fetch_company_profile("005930", market="KOR")

        assert result is not None
        assert result["ticker"] == "005930"
        assert result["name"] == "Samsung Electronics Co., Ltd."
        assert result["market"] == "KOR"
        assert result["sector"] == "Technology"
        assert result["industry"] == "Semiconductors"
        assert result["description"] == "Samsung is a global tech company."

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_fallback_to_short_name(self, mock_ticker_cls):
        """longName 없으면 shortName 사용."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Samsung"}
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_company_profile

        result = fetch_company_profile("005930")
        assert result is not None
        assert result["name"] == "Samsung"

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_no_name_returns_none(self, mock_ticker_cls):
        """name이 없으면 None 반환."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"sector": "Technology"}
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_company_profile

        result = fetch_company_profile("005930")
        assert result is None

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_empty_info_returns_none(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_cls.return_value = mock_ticker

        from app.pipeline.financial_collector import fetch_company_profile

        result = fetch_company_profile("005930")
        assert result is None

    @patch("app.pipeline.financial_collector.yf.Ticker")
    def test_exception_returns_none(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = RuntimeError("API down")

        from app.pipeline.financial_collector import fetch_company_profile

        result = fetch_company_profile("005930")
        assert result is None
