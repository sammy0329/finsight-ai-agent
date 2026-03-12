"""T-505: Supabase financial_metrics, company_profiles upsert 모듈."""

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
