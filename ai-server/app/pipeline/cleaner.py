"""T-108: 데이터 정제 공통 모듈.

HTML 태그 제거, 중복 제거, 빈값 필터 등 데이터 정제 유틸리티를 제공한다.
"""

import html
import re


def remove_html_tags(text: str) -> str:
    """HTML 태그 및 HTML 엔티티를 제거한다.

    Args:
        text: 정제할 텍스트

    Returns:
        태그와 엔티티가 제거된 텍스트
    """
    # HTML 태그 제거
    cleaned = re.sub(r"<[^>]+>", "", text)
    # HTML 엔티티 변환 (&amp; -> &, &lt; -> < 등)
    cleaned = html.unescape(cleaned)
    return cleaned


def deduplicate(items: list[dict], key: str) -> list[dict]:
    """key 필드 기준으로 중복을 제거한다. 첫 번째 항목을 유지한다.

    Args:
        items: 딕셔너리 리스트
        key: 중복 판별 기준 필드명

    Returns:
        중복이 제거된 리스트
    """
    seen: set = set()
    result: list[dict] = []
    for item in items:
        value = item.get(key)
        if value not in seen:
            seen.add(value)
            result.append(item)
    return result


def filter_empty(items: list[dict], required_fields: list[str]) -> list[dict]:
    """required_fields 중 하나라도 비어있으면 해당 항목을 제거한다.

    빈 문자열, None, 공백만 있는 문자열, 키 자체가 없는 경우 모두 빈값으로 취급한다.

    Args:
        items: 딕셔너리 리스트
        required_fields: 반드시 값이 있어야 하는 필드명 리스트

    Returns:
        필터링된 리스트
    """
    result: list[dict] = []
    for item in items:
        valid = True
        for field in required_fields:
            value = item.get(field)
            if value is None:
                valid = False
                break
            if isinstance(value, str) and not value.strip():
                valid = False
                break
        if valid:
            result.append(item)
    return result


def clean_news_items(items: list[dict]) -> list[dict]:
    """뉴스 리스트를 정제한다.

    1. title, description의 HTML 태그/엔티티 제거
    2. link 기준 중복 제거
    3. title, link 필수 필드 빈값 필터

    Args:
        items: 뉴스 딕셔너리 리스트

    Returns:
        정제된 뉴스 리스트
    """
    # 1. HTML 태그 제거
    cleaned: list[dict] = []
    for item in items:
        new_item = dict(item)
        for field in ("title", "description"):
            if field in new_item and isinstance(new_item[field], str):
                new_item[field] = remove_html_tags(new_item[field])
        cleaned.append(new_item)

    # 2. 중복 제거 (link 기준)
    deduped = deduplicate(cleaned, "link")

    # 3. 빈값 필터 (title, link 필수)
    return filter_empty(deduped, ["title", "link"])
