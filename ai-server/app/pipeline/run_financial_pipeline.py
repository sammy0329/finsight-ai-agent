"""T-506: 재무 데이터 파이프라인 통합 실행 스크립트.

CLI 실행:
    python -m app.pipeline.run_financial_pipeline
"""

import logging
import os
import sys

from app.pipeline.financial_collector import fetch_company_profile, fetch_financial_metrics
from app.pipeline.supabase_store import upsert_company_profiles, upsert_financial_metrics

logger = logging.getLogger(__name__)

# 수집 대상 종목 (ticker, market)
DEFAULT_TICKERS = [
    ("005930", "KOR"),  # 삼성전자
    ("000660", "KOR"),  # SK하이닉스
    ("035420", "KOR"),  # NAVER
    ("035720", "KOR"),  # 카카오
    ("009150", "KOR"),  # 삼성전기
    ("AAPL", "US"),
    ("MSFT", "US"),
    ("NVDA", "US"),
    ("GOOGL", "US"),
    ("AMZN", "US"),
]


def run_financial_pipeline(config: dict) -> dict:
    """재무 데이터 파이프라인을 실행한다.

    Args:
        config: supabase_url, supabase_key, tickers(optional) 포함 dict.

    Returns:
        metrics_collected, metrics_upserted, profiles_collected, profiles_upserted 포함 dict.
    """
    stats = {
        "metrics_collected": 0,
        "metrics_upserted": 0,
        "profiles_collected": 0,
        "profiles_upserted": 0,
    }

    tickers = config.get("tickers", DEFAULT_TICKERS)
    url = config["supabase_url"]
    key = config["supabase_key"]

    metrics_list: list[dict] = []
    profiles_list: list[dict] = []

    for ticker, market in tickers:
        metrics = fetch_financial_metrics(ticker, market)
        if metrics:
            metrics_list.append(metrics)
            stats["metrics_collected"] += 1

        profile = fetch_company_profile(ticker, market)
        if profile:
            profiles_list.append(profile)
            stats["profiles_collected"] += 1

    if metrics_list:
        stats["metrics_upserted"] = upsert_financial_metrics(url, key, metrics_list)

    if profiles_list:
        stats["profiles_upserted"] = upsert_company_profiles(url, key, profiles_list)

    return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = {
        "supabase_url": os.environ["SUPABASE_URL"],
        "supabase_key": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    }

    logger.info("재무 파이프라인 시작")
    result = run_financial_pipeline(config)
    logger.info("재무 파이프라인 완료 — %s", result)

    success = result["metrics_upserted"] > 0
    sys.exit(0 if success else 1)
