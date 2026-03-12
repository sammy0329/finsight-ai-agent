"""Supabase upsert 모듈.

T-505: financial_metrics, company_profiles
T-602: daily_prices
T-605: market_indices, fx_rates
"""

import logging

from supabase import create_client

logger = logging.getLogger(__name__)


def upsert_financial_metrics(url: str, key: str, metrics: list[dict]) -> int:
    """financial_metrics 테이블에 upsert한다.

    Returns:
        삽입/갱신된 레코드 수. 오류 시 0.
    """
    if not metrics:
        return 0
    try:
        client = create_client(url, key)
        result = (
            client.table("financial_metrics").upsert(metrics, on_conflict="ticker,period").execute()
        )
        return len(result.data)
    except Exception:
        logger.warning("financial_metrics upsert 실패", exc_info=True)
        return 0


def upsert_company_profiles(url: str, key: str, profiles: list[dict]) -> int:
    """company_profiles 테이블에 upsert한다.

    Returns:
        삽입/갱신된 레코드 수. 오류 시 0.
    """
    if not profiles:
        return 0
    try:
        client = create_client(url, key)
        result = client.table("company_profiles").upsert(profiles, on_conflict="ticker").execute()
        return len(result.data)
    except Exception:
        logger.warning("company_profiles upsert 실패", exc_info=True)
        return 0


def upsert_daily_prices(url: str, key: str, prices: list[dict]) -> int:
    """daily_prices 테이블에 upsert한다.

    Returns:
        삽입/갱신된 레코드 수. 오류 시 0.
    """
    if not prices:
        return 0
    try:
        client = create_client(url, key)
        result = client.table("daily_prices").upsert(prices, on_conflict="ticker,date").execute()
        return len(result.data)
    except Exception:
        logger.warning("daily_prices upsert 실패", exc_info=True)
        return 0


def upsert_market_indices(url: str, key: str, indices: list[dict]) -> int:
    """market_indices 테이블에 upsert한다.

    Returns:
        삽입/갱신된 레코드 수. 오류 시 0.
    """
    if not indices:
        return 0
    try:
        client = create_client(url, key)
        result = client.table("market_indices").upsert(indices, on_conflict="symbol,date").execute()
        return len(result.data)
    except Exception:
        logger.warning("market_indices upsert 실패", exc_info=True)
        return 0


def upsert_fx_rates(url: str, key: str, rates: list[dict]) -> int:
    """fx_rates 테이블에 upsert한다.

    Returns:
        삽입/갱신된 레코드 수. 오류 시 0.
    """
    if not rates:
        return 0
    try:
        client = create_client(url, key)
        result = client.table("fx_rates").upsert(rates, on_conflict="pair,date").execute()
        return len(result.data)
    except Exception:
        logger.warning("fx_rates upsert 실패", exc_info=True)
        return 0
