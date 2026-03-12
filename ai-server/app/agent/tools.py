"""T-220 ~ T-223: Multi-tool Agent 도구 정의.

4개의 LangChain Tool을 정의한다:
- search_news_tool: ChromaDB RAG 뉴스 검색
- get_dart_tool: DART 공시 목록 조회
- get_price_tool: Yahoo Finance 실시간 가격 조회
- price_anomaly_tool: 수익률 Z-score 이상 감지
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import httpx
from langchain_core.tools import tool

from app.agent.retriever import get_retriever
from app.core.config import settings

# ── T-220: search_news ───────────────────────────────────────────────


def search_news(query: str, market: str = "KOR") -> str:
    """ChromaDB에서 관련 뉴스 청크를 검색한다.

    Args:
        query: 검색 키워드.
        market: 시장 코드 ("KOR" 또는 "US").

    Returns:
        검색된 뉴스 청크 문자열 또는 폴백 메시지.
    """
    try:
        retriever = get_retriever(
            chroma_host=settings.chroma_host,
            chroma_port=settings.chroma_port,
            market=market,
        )
        docs = retriever.invoke(query)
    except Exception:
        return "뉴스 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    if not docs:
        return "관련 뉴스를 찾을 수 없습니다."

    chunks = []
    for doc in docs:
        source = doc.metadata.get("source", "")
        text = doc.page_content
        if source:
            chunks.append(f"{text}\n(출처: {source})")
        else:
            chunks.append(text)

    return "\n\n".join(chunks)


# ── T-221: get_dart_filings ──────────────────────────────────────────

_DART_BASE_URL = "https://opendart.fss.or.kr/api/list.json"
_MAX_FILINGS = 10


def get_dart_filings(corp_name: str) -> str:
    """DART API에서 최근 30일 공시 목록을 조회한다.

    Args:
        corp_name: 기업명.

    Returns:
        포맷팅된 공시 목록 문자열 또는 오류 메시지.
    """
    dart_api_key = os.environ.get("DART_API_KEY", "")
    bgn_de = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

    try:
        resp = httpx.get(
            _DART_BASE_URL,
            params={
                "crtfc_key": dart_api_key,
                "corp_name": corp_name,
                "bgn_de": bgn_de,
                "page_count": 20,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return "DART 공시 조회 중 오류가 발생했습니다."

    status = data.get("status", "")
    if status != "000":
        return f"{corp_name}의 최근 공시를 찾을 수 없습니다."

    filings = data.get("list", [])
    if not filings:
        return f"{corp_name}의 최근 30일간 공시가 없습니다."

    filings = filings[:_MAX_FILINGS]

    lines = [f"[{corp_name} 최근 공시 ({len(filings)}건)]"]
    for f in filings:
        report_nm = f.get("report_nm", "")
        rcept_dt = f.get("rcept_dt", "")
        lines.append(f"- {report_nm} ({rcept_dt})")

    return "\n".join(lines)


# ── T-222: get_price ─────────────────────────────────────────────────

_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"


def get_price(ticker: str) -> str:
    """Yahoo Finance에서 현재 가격 정보를 조회한다.

    Args:
        ticker: 종목 티커 (예: "005930.KS", "AAPL").

    Returns:
        포맷팅된 가격 정보 문자열 또는 오류 메시지.
    """
    try:
        resp = httpx.get(
            _YAHOO_CHART_URL.format(ticker=ticker),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return f"{ticker} 가격 조회 중 오류가 발생했습니다."

    try:
        result = data["chart"]["result"]
        if not result:
            return f"{ticker} 가격 정보를 찾을 수 없습니다."

        meta = result[0]["meta"]
        price = meta["regularMarketPrice"]
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
        currency = meta.get("currency", "")
        symbol = meta.get("symbol", ticker)

        if prev_close and prev_close != 0:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            sign = "+" if change >= 0 else ""
            return (
                f"[{symbol}] 현재가: {price:,.2f} {currency} | "
                f"전일대비: {sign}{change:,.2f} ({sign}{change_pct:.2f}%)"
            )
        else:
            return f"[{symbol}] 현재가: {price:,.2f} {currency}"
    except (KeyError, TypeError, IndexError):
        return f"{ticker} 가격 정보를 찾을 수 없습니다."


# ── T-223: Z-score 계산 및 이상 감지 ─────────────────────────────────


def calculate_zscore(returns: list[float]) -> float | None:
    """수익률 리스트의 최근 값에 대한 Z-score를 계산한다.

    Args:
        returns: 일별 수익률 리스트.

    Returns:
        Z-score 값. 데이터가 5개 미만이거나 표준편차가 0이면 None.
    """
    if len(returns) < 5:
        return None

    import statistics

    mean = statistics.mean(returns)
    stdev = statistics.pstdev(returns)  # 모집단 표준편차

    if stdev == 0:
        return None

    return (returns[-1] - mean) / stdev


def detect_price_anomaly(ticker: str) -> str:
    """FinanceDataReader로 최근 20일 수익률의 Z-score 이상을 감지한다.

    Args:
        ticker: 종목 티커.

    Returns:
        이상 감지 결과 문자열.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=40)  # 여유롭게 40일치 조회
        df = fdr.DataReader(ticker, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    except Exception:
        return f"{ticker} 가격 데이터 조회 중 오류가 발생했습니다."

    if df is None or df.empty or len(df) < 5:
        return f"{ticker}의 가격 데이터가 부족합니다 (최소 5일 필요)."

    # 최근 20일로 제한
    df = df.tail(20)
    closes = df["Close"].tolist()

    # 일별 수익률 계산
    returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] != 0:
            returns.append((closes[i] - closes[i - 1]) / closes[i - 1])

    if len(returns) < 5:
        return f"{ticker}의 수익률 데이터가 부족합니다 (최소 5일 필요)."

    z = calculate_zscore(returns)
    if z is None:
        return f"{ticker}의 수익률 변동이 없어 Z-score를 계산할 수 없습니다."

    latest_return = returns[-1] * 100
    abs_z = abs(z)

    if abs_z > 2:
        direction = "급등" if z > 0 else "급락"
        return (
            f"[이상 감지] {ticker}: 최근 수익률 {latest_return:+.2f}%로 "
            f"{direction} 감지 (Z-score: {z:.2f}, |Z| > 2)"
        )
    else:
        return (
            f"[정상] {ticker}: 최근 수익률 {latest_return:+.2f}%로 특이사항 없음 (Z-score: {z:.2f})"
        )


# ── T-226: 구조화된 이상 감지 결과 (API 응답용) ───────────────────────


def detect_price_anomaly_json(ticker: str) -> dict:
    """가격 이상 감지 결과를 구조화된 dict로 반환한다.

    Args:
        ticker: 종목 티커.

    Returns:
        is_anomaly, zscore, direction, latest_return_pct, message 포함 dict.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=40)
        df = fdr.DataReader(ticker, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    except Exception:
        return {
            "ticker": ticker,
            "is_anomaly": False,
            "zscore": None,
            "direction": None,
            "latest_return_pct": None,
            "message": "가격 데이터 조회 실패",
        }

    if df is None or df.empty or len(df) < 5:
        return {
            "ticker": ticker,
            "is_anomaly": False,
            "zscore": None,
            "direction": None,
            "latest_return_pct": None,
            "message": "데이터 부족",
        }

    df = df.tail(20)
    closes = df["Close"].tolist()
    returns = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]

    if len(returns) < 5:
        return {
            "ticker": ticker,
            "is_anomaly": False,
            "zscore": None,
            "direction": None,
            "latest_return_pct": None,
            "message": "수익률 데이터 부족",
        }

    z = calculate_zscore(returns)
    if z is None:
        return {
            "ticker": ticker,
            "is_anomaly": False,
            "zscore": None,
            "direction": None,
            "latest_return_pct": None,
            "message": "표준편차 0 (변동 없음)",
        }

    latest_return_pct = returns[-1] * 100
    is_anomaly = abs(z) > 2
    direction = ("급등" if z > 0 else "급락") if is_anomaly else None

    return {
        "ticker": ticker,
        "is_anomaly": is_anomaly,
        "zscore": round(z, 2),
        "direction": direction,
        "latest_return_pct": round(latest_return_pct, 2),
        "message": (
            f"{direction} 감지 (Z-score: {z:.2f})" if is_anomaly else f"정상 (Z-score: {z:.2f})"
        ),
    }


# ── LangChain Tool 래핑 ─────────────────────────────────────────────


@tool
def search_news_tool(query: str, market: str = "KOR") -> str:
    """관련 금융 뉴스를 검색합니다. 키워드를 입력하면 ChromaDB에서 관련 뉴스를 찾아줍니다."""
    return search_news(query, market)


@tool
def get_dart_tool(corp_name: str) -> str:
    """DART에서 기업의 최근 30일 공시 목록을 조회합니다. 기업명을 입력하세요."""
    return get_dart_filings(corp_name)


@tool
def get_price_tool(ticker: str) -> str:
    """Yahoo Finance에서 종목의 현재 가격을 조회합니다. 티커를 입력하세요 (예: 005930.KS, AAPL)."""
    return get_price(ticker)


@tool
def price_anomaly_tool(ticker: str) -> str:
    """최근 20일 수익률의 Z-score를 계산하여 가격 이상을 감지합니다. 티커를 입력하세요."""
    return detect_price_anomaly(ticker)
