"""T-107: NewsAPI 미국 뉴스 수집 모듈.

NewsAPI(newsapi.org)를 통해 영어권 뉴스를 수집한다.
[Removed] 기사를 필터링하고, 오류 발생 시 빈 리스트를 반환한다.
"""

import logging

import requests

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_us_news(api_key: str, query: str, date: str) -> list[dict]:
    """NewsAPI를 통해 미국/영어권 뉴스를 수집한다.

    Args:
        api_key: NewsAPI 인증 키
        query: 검색 키워드
        date: 조회 날짜 (YYYY-MM-DD)

    Returns:
        뉴스 dict 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        resp = requests.get(
            NEWSAPI_URL,
            params={
                "apiKey": api_key,
                "q": query,
                "from": date,
                "to": date,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.warning("Failed to fetch US news for query=%s", query, exc_info=True)
        return []

    if data.get("status") != "ok":
        return []

    articles = data.get("articles", [])
    if not articles:
        return []

    results: list[dict] = []
    for article in articles:
        if article.get("title") == "[Removed]":
            continue
        results.append(
            {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "publishedAt": article.get("publishedAt", ""),
                "url": article.get("url", ""),
            }
        )

    return results
