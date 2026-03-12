"""T-503, T-504: yfinance 기반 재무지표·기업개요 수집 모듈."""

import logging
from datetime import date

import yfinance as yf

logger = logging.getLogger(__name__)


def current_quarter() -> str:
    """현재 분기를 "YYYYQN" 형식으로 반환한다."""
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    return f"{today.year}Q{quarter}"


def _yf_symbol(ticker: str, market: str) -> str:
    """market에 따라 yfinance 심볼을 결정한다."""
    return ticker if market == "US" else f"{ticker}.KS"


def fetch_financial_metrics(ticker: str, market: str = "KOR") -> dict | None:
    """yfinance로 분기 재무지표를 수집한다.

    Returns:
        ticker, period, per, pbr, roe, eps, revenue, op_income, net_income 포함 dict.
        오류 발생 시 None 반환.
    """
    try:
        info = yf.Ticker(_yf_symbol(ticker, market)).info
        if not info:
            return None
        return {
            "ticker": ticker,
            "period": current_quarter(),
            "per": info.get("trailingPE"),
            "pbr": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "eps": info.get("trailingEps"),
            "revenue": info.get("totalRevenue"),
            "op_income": info.get("operatingIncome"),
            "net_income": info.get("netIncomeToCommon"),
        }
    except Exception:
        logger.warning("재무지표 수집 실패: ticker=%s", ticker, exc_info=True)
        return None


def fetch_company_profile(ticker: str, market: str = "KOR") -> dict | None:
    """yfinance로 기업 개요를 수집한다.

    Returns:
        ticker, name, market, sector, industry, description 포함 dict.
        오류 발생 시 None 반환.
    """
    try:
        info = yf.Ticker(_yf_symbol(ticker, market)).info
        if not info:
            return None
        name = info.get("longName") or info.get("shortName")
        if not name:
            return None
        return {
            "ticker": ticker,
            "name": name,
            "market": market,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "description": info.get("longBusinessSummary"),
        }
    except Exception:
        logger.warning("기업 개요 수집 실패: ticker=%s", ticker, exc_info=True)
        return None
