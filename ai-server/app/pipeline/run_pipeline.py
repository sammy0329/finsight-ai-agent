"""T-115 / T-601~605: 파이프라인 통합 실행 스크립트.

뉴스 수집 -> 정제 -> 메타데이터 부착 -> 청킹 -> 임베딩 -> ChromaDB upsert
+ 주가/지수/환율 수집 -> Supabase upsert
전체 파이프라인을 실행하고 결과 통계를 반환한다.

CLI 실행:
    python -m app.pipeline.run_pipeline
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from app.pipeline.chroma_client import get_chroma_client, get_or_create_collection
from app.pipeline.chunker import chunk_news_item
from app.pipeline.cleaner import clean_news_items
from app.pipeline.dedup import deduplicate_by_url
from app.pipeline.embedder import embed_documents
from app.pipeline.market_collector import fetch_fx_rates, fetch_market_indices
from app.pipeline.metadata_builder import build_news_metadata
from app.pipeline.news_collector import fetch_naver_news_multi
from app.pipeline.newsapi_collector import fetch_us_news_multi
from app.pipeline.query_config import KOR_QUERIES, US_QUERIES
from app.pipeline.stock_collector import fetch_stock_data
from app.pipeline.supabase_store import (
    upsert_daily_prices,
    upsert_fx_rates,
    upsert_market_indices,
)
from app.pipeline.vector_store import upsert_chunks

KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)


def run_pipeline(config: dict) -> dict:
    """전체 RAG 파이프라인을 실행한다.

    각 단계 실패 시 로그를 기록하고 다음 단계로 진행한다 (파이프라인 중단 방지).

    Args:
        config: 파이프라인 설정
            - market: "KOR" | "US"
            - date: "YYYY-MM-DD"
            - tickers: list[str]
            - query: str
            - openai_api_key: str
            - chroma_host: str
            - chroma_port: int

    Returns:
        {"collected": int, "cleaned": int, "chunked": int, "upserted": int}
    """
    stats = {"collected": 0, "cleaned": 0, "chunked": 0, "upserted": 0, "deduplicated": 0}

    # ChromaDB 초기화
    try:
        client = get_chroma_client(config["chroma_host"], config["chroma_port"])
        collection = get_or_create_collection(client, f"news_{config['market'].lower()}")
    except Exception:
        logger.exception("ChromaDB 초기화 실패")
        return stats

    # 1. 수집
    try:
        if config["market"] == "KOR":
            fetched = fetch_naver_news_multi(
                queries=KOR_QUERIES,
                client_id=config["naver_client_id"],
                client_secret=config["naver_client_secret"],
                date=config["date"].replace("-", ""),
            )
            raw_items = deduplicate_by_url(fetched, "link")
        else:
            fetched = fetch_us_news_multi(
                queries=US_QUERIES,
                api_key=config["news_api_key"],
                date=config["date"],
            )
            raw_items = deduplicate_by_url(fetched, "url")
        stats["deduplicated"] = len(fetched) - len(raw_items)
        stats["collected"] = len(raw_items)
    except Exception:
        logger.exception("뉴스 수집 실패")
        return stats

    if not raw_items:
        return stats

    # 2. 정제
    try:
        cleaned_items = clean_news_items(raw_items)
        stats["cleaned"] = len(cleaned_items)
    except Exception:
        logger.exception("데이터 정제 실패")
        return stats

    if not cleaned_items:
        return stats

    # 3. 메타데이터 부착 + 청킹
    all_chunks: list[dict] = []
    source = "naver_news" if config["market"] == "KOR" else "newsapi"
    for item in cleaned_items:
        try:
            metadata = build_news_metadata(item, source, config["market"])
            chunks = chunk_news_item(item, metadata)
            all_chunks.extend(chunks)
        except Exception:
            logger.exception("청킹 실패: %s", item.get("title", "unknown"))
            continue

    stats["chunked"] = len(all_chunks)

    if not all_chunks:
        return stats

    # 4. 임베딩
    try:
        documents = [c["document"] for c in all_chunks]
        embeddings = embed_documents(documents, api_key=config["openai_api_key"])
        for i, chunk in enumerate(all_chunks):
            chunk["embedding"] = embeddings[i]
    except Exception:
        logger.exception("임베딩 실패")
        return stats

    # 5. ChromaDB upsert
    try:
        upserted = upsert_chunks(collection, all_chunks)
        stats["upserted"] = upserted
    except Exception:
        logger.exception("ChromaDB upsert 실패")

    return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    run_date = os.getenv("PIPELINE_DATE") or datetime.now(KST).strftime("%Y-%m-%d")
    market = os.getenv("PIPELINE_MARKET", "ALL")
    markets = ["KOR", "US"] if market == "ALL" else [market]

    config_base = {
        "date": run_date,
        "tickers": [],
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "naver_client_id": os.getenv("NAVER_CLIENT_ID", ""),
        "naver_client_secret": os.getenv("NAVER_CLIENT_SECRET", ""),
        "dart_api_key": os.getenv("DART_API_KEY", ""),
        "news_api_key": os.getenv("NEWS_API_KEY", ""),
        "chroma_host": os.getenv("CHROMA_HOST", "localhost"),
        "chroma_port": int(os.getenv("CHROMA_PORT", "8001")),
    }

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    total: dict[str, int] = {
        "collected": 0,
        "cleaned": 0,
        "chunked": 0,
        "upserted": 0,
        "deduplicated": 0,
    }
    success = True

    for m in markets:
        logger.info("파이프라인 시작 — market=%s, date=%s", m, run_date)
        result = run_pipeline({**config_base, "market": m})
        logger.info("파이프라인 완료 — %s", result)
        for key in total:
            total[key] += result.get(key, 0)
        if result["upserted"] == 0:
            logger.warning("market=%s upsert 결과 없음", m)
            success = False

    # ------------------------------------------------------------------ #
    # T-602: 주가 데이터 Supabase 적재
    # ------------------------------------------------------------------ #
    tickers = config_base.get("tickers", [])
    if tickers:
        logger.info("주가 수집 시작 — tickers=%s", tickers)
        prices = fetch_stock_data(tickers, run_date, run_date)
        if prices and supabase_url:
            cnt = upsert_daily_prices(supabase_url, supabase_key, prices)
            logger.info("daily_prices upsert 완료 — %d건", cnt)

    # ------------------------------------------------------------------ #
    # T-603/T-604: 지수/환율 수집 + Supabase 적재
    # ------------------------------------------------------------------ #
    for m in markets:
        logger.info("지수 수집 시작 — market=%s", m)
        indices = fetch_market_indices(run_date, market=m)
        if indices and supabase_url:
            cnt = upsert_market_indices(supabase_url, supabase_key, indices)
            logger.info("market_indices upsert 완료 — market=%s, %d건", m, cnt)

    if "KOR" in markets:
        logger.info("환율 수집 시작")
        fx = fetch_fx_rates(run_date)
        if fx and supabase_url:
            cnt = upsert_fx_rates(supabase_url, supabase_key, fx)
            logger.info("fx_rates upsert 완료 — %d건", cnt)

    logger.info("최종 통계 — %s", total)
    sys.exit(0 if success else 1)
