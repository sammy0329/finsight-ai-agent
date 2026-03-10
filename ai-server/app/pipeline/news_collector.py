"""T-106: Naver Search API 뉴스 수집 모듈.

네이버 검색 API를 통해 한국어 뉴스를 수집한다.
HTML 태그를 제거하고, 오류 발생 시 빈 리스트를 반환한다.
"""

import logging
import re
import time

import requests

logger = logging.getLogger(__name__)

NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


def _strip_html(text: str) -> str:
    """HTML 태그를 제거한다."""
    return re.sub(r"<[^>]+>", "", text)


def fetch_naver_news(
    client_id: str,
    client_secret: str,
    query: str,
    date: str,
) -> list[dict]:
    """네이버 뉴스 검색 API를 통해 뉴스를 수집한다.

    Args:
        client_id: 네이버 API 클라이언트 ID
        client_secret: 네이버 API 클라이언트 시크릿
        query: 검색 키워드
        date: 조회 날짜 (YYYYMMDD) - 정렬 기준용

    Returns:
        뉴스 dict 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        resp = requests.get(
            NAVER_SEARCH_URL,
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={
                "query": query,
                "display": 50,
                "sort": "date",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.warning("Failed to fetch Naver news for query=%s", query, exc_info=True)
        return []

    items = data.get("items", [])
    if not items:
        return []

    results: list[dict] = []
    for item in items:
        results.append(
            {
                "title": _strip_html(item.get("title", "")),
                "description": _strip_html(item.get("description", "")),
                "pubDate": item.get("pubDate", ""),
                "link": item.get("link", ""),
            }
        )

    return results


def fetch_naver_news_multi(
    queries: list[dict],
    client_id: str,
    client_secret: str,
    date: str,
) -> list[dict]:
    """여러 쿼리로 Naver 뉴스를 수집하고 각 기사에 category를 부착한다.

    Args:
        queries: [{"category": str, "query": str}, ...]
        client_id: 네이버 API 클라이언트 ID
        client_secret: 네이버 API 클라이언트 시크릿
        date: 조회 날짜 (YYYYMMDD)

    Returns:
        category가 부착된 뉴스 dict 리스트
    """
    all_items: list[dict] = []
    for i, q in enumerate(queries):
        if i > 0:
            time.sleep(0.5)
        items = fetch_naver_news(
            client_id=client_id,
            client_secret=client_secret,
            query=q["query"],
            date=date,
        )
        for item in items:
            item["category"] = q["category"]
        all_items.extend(items)
    return all_items
