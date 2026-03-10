"""T-115: 파이프라인 통합 실행 스크립트.

뉴스 수집 -> 정제 -> 메타데이터 부착 -> 청킹 -> 임베딩 -> ChromaDB upsert
전체 파이프라인을 실행하고 결과 통계를 반환한다.
"""

import logging

from app.pipeline.chroma_client import get_chroma_client, get_or_create_collection
from app.pipeline.chunker import chunk_news_item
from app.pipeline.cleaner import clean_news_items
from app.pipeline.embedder import embed_documents
from app.pipeline.metadata_builder import build_news_metadata
from app.pipeline.news_collector import fetch_naver_news
from app.pipeline.vector_store import upsert_chunks

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
    stats = {"collected": 0, "cleaned": 0, "chunked": 0, "upserted": 0}

    # ChromaDB 초기화
    try:
        client = get_chroma_client(config["chroma_host"], config["chroma_port"])
        collection = get_or_create_collection(client, f"news_{config['market'].lower()}")
    except Exception:
        logger.exception("ChromaDB 초기화 실패")
        return stats

    # 1. 수집
    try:
        raw_items = fetch_naver_news(
            client_id="",
            client_secret="",
            query=config["query"],
            date=config["date"].replace("-", ""),
        )
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
