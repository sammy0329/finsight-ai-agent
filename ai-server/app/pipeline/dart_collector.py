"""T-105: OpenDart API 기업 공시 수집 모듈.

DART(전자공시시스템) OpenAPI를 통해 기업 공시 목록을 수집한다.
오류 발생 시 빈 리스트를 반환하여 파이프라인이 중단되지 않도록 한다.
"""

import logging

import requests

logger = logging.getLogger(__name__)

DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"


def fetch_dart_disclosures(api_key: str, date: str) -> list[dict]:
    """주어진 날짜의 기업 공시 목록을 수집한다.

    Args:
        api_key: DART OpenAPI 인증 키
        date: 조회 날짜 (YYYYMMDD)

    Returns:
        공시 dict 리스트. 오류 발생 시 빈 리스트 반환.
    """
    try:
        resp = requests.get(
            DART_LIST_URL,
            params={
                "crtfc_key": api_key,
                "bgn_de": date,
                "end_de": date,
                "page_count": 100,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.warning("Failed to fetch DART disclosures for date=%s", date, exc_info=True)
        return []

    if data.get("status") != "000":
        return []

    items = data.get("list", [])
    if not items:
        return []

    results: list[dict] = []
    for item in items:
        results.append(
            {
                "title": item.get("report_nm", ""),
                "corp_name": item.get("corp_name", ""),
                "rcept_dt": item.get("rcept_dt", ""),
                "report_nm": item.get("report_nm", ""),
            }
        )

    return results
