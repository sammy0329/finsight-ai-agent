"""T-123: 뉴스 중복 제거 모듈.

URL 등 특정 필드를 기준으로 중복 기사를 제거한다.
"""


def deduplicate_by_url(items: list[dict], key_field: str) -> list[dict]:
    """key_field 기준으로 중복 제거. 먼저 나온 항목 우선.

    Args:
        items: 뉴스 딕셔너리 리스트
        key_field: 중복 판단 기준 필드명

    Returns:
        중복이 제거된 리스트 (원본 순서 유지)
    """
    seen: set = set()
    result: list[dict] = []
    for item in items:
        key = item.get(key_field)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
