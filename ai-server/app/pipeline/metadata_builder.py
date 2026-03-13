"""T-109: 메타데이터 부착 모듈.

뉴스 데이터에 source, sentiment, tickers 등 메타데이터를 부착한다.
"""

import re
from datetime import datetime

POSITIVE_KEYWORDS = ["상승", "급등", "호실적", "흑자", "성장", "surge", "bullish", "profit"]
NEGATIVE_KEYWORDS = ["하락", "급락", "적자", "손실", "위기", "drop", "bearish", "loss"]

# 미국 시장에서 티커로 오인될 수 있는 일반 영단어
_US_STOP_WORDS = {
    "THE",
    "AND",
    "FOR",
    "ARE",
    "BUT",
    "NOT",
    "YOU",
    "ALL",
    "CAN",
    "HER",
    "WAS",
    "ONE",
    "OUR",
    "OUT",
    "HAS",
    "HIS",
    "HOW",
    "ITS",
    "MAY",
    "NEW",
    "NOW",
    "OLD",
    "SEE",
    "WAY",
    "WHO",
    "DID",
    "GET",
    "HAS",
    "HIM",
    "LET",
    "SAY",
    "SHE",
    "TOO",
    "USE",
    "DAD",
    "MOM",
    "SET",
    "TOP",
    "RED",
    "BIG",
    "CEO",
    "CFO",
    "IPO",
    "ETF",
    "GDP",
    "FDA",
    "IS",
    "IT",
    "IN",
    "ON",
    "AT",
    "TO",
    "AS",
    "IF",
    "OF",
}


def detect_sentiment(text: str) -> str:
    """키워드 기반 단순 감성 분류.

    Args:
        text: 분석할 텍스트

    Returns:
        "positive", "negative", "neutral" 중 하나
    """
    if not text:
        return "neutral"

    text_lower = text.lower()
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw.lower() in text_lower)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw.lower() in text_lower)

    if pos_count > neg_count:
        return "positive"
    if neg_count > pos_count:
        return "negative"
    return "neutral"


def extract_tickers(text: str, market: str) -> list[str]:
    """텍스트에서 종목 코드 패턴을 추출한다.

    Args:
        text: 분석할 텍스트
        market: "KOR" 또는 "US"

    Returns:
        추출된 종목 코드 리스트 (중복 제거)
    """
    if not text:
        return []

    if market == "KOR":
        # 6자리 숫자만 추출 (앞뒤가 숫자가 아닌 경우)
        matches = re.findall(r"(?<!\d)\d{6}(?!\d)", text)
    elif market == "US":
        # 대문자 알파벳 2~5자 (단어 경계 기준)
        matches = re.findall(r"\b([A-Z]{2,5})\b", text)
        matches = [m for m in matches if m not in _US_STOP_WORDS]
    else:
        return []

    # 중복 제거 (순서 유지)
    seen: set[str] = set()
    result: list[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def build_news_metadata(item: dict, source: str, market: str) -> dict:
    """뉴스 항목에 메타데이터를 생성한다.

    Args:
        item: 뉴스 딕셔너리 (title, description, pubDate 등)
        source: 뉴스 소스 ("naver_news", "newsapi" 등)
        market: 시장 ("KOR", "US")

    Returns:
        메타데이터 딕셔너리
    """
    # 감성 분석용 텍스트 결합
    analysis_text = " ".join(filter(None, [item.get("title", ""), item.get("description", "")]))

    tickers = extract_tickers(analysis_text, market)
    url = item.get("link") or item.get("url") or item.get("originallink") or ""
    return {
        "source": source,
        "published_at": item.get("pubDate", ""),
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "market": market,
        "related_tickers": ",".join(tickers),
        "category": item.get("category", "general"),
        "sentiment": detect_sentiment(analysis_text),
        "url": url,
    }
