"""T-609: 4종 리포트 생성 파이프라인.

리포트 타입별 트리거 시각 (KST):
- KOR_PREMARKET: 08:00 (한국 장 전 브리프)
- KOR_CLOSE:    16:30 (한국 장 마감 리포트)
- US_PREMARKET: 22:30 (미국 장 전 브리프)
- US_CLOSE:     07:00 (미국 장 마감 리포트)

파이프라인 흐름:
1. Supabase에서 시장 지수·환율·종목 최근 종가 조회
2. ChromaDB에서 최신 뉴스 검색
3. OpenAI로 시장 요약 생성
4. market_snapshots upsert
5. watchlist 기반 사용자 알림 삽입
"""

from __future__ import annotations

import logging
from typing import Literal

from openai import OpenAI
from supabase import create_client

logger = logging.getLogger(__name__)

ReportType = Literal["KOR_PREMARKET", "KOR_CLOSE", "US_PREMARKET", "US_CLOSE"]

REPORT_CONFIG: dict[str, dict] = {
    "KOR_PREMARKET": {"market": "KOR", "label": "한국 장 전 브리프"},
    "KOR_CLOSE": {"market": "KOR", "label": "한국 장 마감 리포트"},
    "US_PREMARKET": {"market": "US", "label": "미국 장 전 브리프"},
    "US_CLOSE": {"market": "US", "label": "미국 장 마감 리포트"},
}

# market 코드 → watchlist.market 컬럼 값 매핑 (프론트엔드 저장 형식)
_MARKET_VALUES: dict[str, list[str]] = {
    "KOR": ["KOSPI", "KOSDAQ"],
    "US": ["NASDAQ", "NYSE", "S&P500", "NYSE Arca", "NYSE MKT"],
}

# symbol → payload key 매핑
_INDEX_KEY_MAP: dict[str, str] = {
    "^KS11": "kospi",
    "^KQ11": "kosdaq",
    "^GSPC": "sp500",
    "^IXIC": "nasdaq",
    "^DJI": "dow",
}


# ── 순수 함수 ──────────────────────────────────────────────────────────────


def build_market_section(indices: list[dict], fx_rates: list[dict]) -> dict:
    """지수·환율 데이터로 market payload 섹션을 빌드한다.

    Args:
        indices: symbol, name, close, change_pct 포함 지수 리스트.
        fx_rates: pair, rate 포함 환율 리스트.

    Returns:
        market payload dict.
    """
    market: dict = {}

    for idx in indices:
        key = _INDEX_KEY_MAP.get(idx.get("symbol", ""))
        if key:
            market[key] = {
                "value": idx["close"],
                "change_pct": idx.get("change_pct", 0.0),
            }

    for fx in fx_rates:
        pair = fx.get("pair", "")
        if pair == "USD/KRW":
            market["usdkrw"] = fx["rate"]
        elif pair == "EUR/KRW":
            market["eurkrw"] = fx["rate"]

    return market


def build_stocks_section(
    prices: list[dict],
    sectors: dict[str, str],
    anomalies: dict[str, dict],
    news_summaries: dict[str, dict],
) -> list[dict]:
    """종목 가격·섹터·이상감지·뉴스요약으로 stocks payload 섹션을 빌드한다.

    Args:
        prices: ticker, name, close, change_pct 포함 리스트.
        sectors: ticker → sector 매핑.
        anomalies: ticker → {zscore, is_anomaly} 매핑.
        news_summaries: ticker → {text, url} 매핑.

    Returns:
        stocks payload 리스트.
    """
    stocks = []
    for p in prices:
        ticker = p["ticker"]
        anomaly = anomalies.get(ticker, {})
        news = news_summaries.get(ticker, {})
        stocks.append(
            {
                "ticker": ticker,
                "name": p.get("name", ""),
                "sector": sectors.get(ticker, ""),
                "close": p["close"],
                "change_pct": p.get("change_pct", 0.0),
                "zscore": anomaly.get("zscore"),
                "price_anomaly": anomaly.get("is_anomaly", False),
                "news_summary": news.get("text", "") if isinstance(news, dict) else news,
                "news_url": news.get("url", "") if isinstance(news, dict) else "",
            }
        )
    return stocks


def build_payload(report_type: ReportType, config: dict) -> dict:
    """리포트 payload 전체를 빌드한다.

    Supabase에서 지수·환율·종목 종가를 읽고, ChromaDB에서 뉴스를 검색하며,
    OpenAI로 시장 요약을 생성하여 JSONB payload를 구성한다.

    Args:
        report_type: 리포트 타입.
        config: supabase_url, supabase_key, openai_api_key, chroma_host,
                chroma_port, date 포함 dict.

    Returns:
        market_summary, market, stocks, top_news 포함 payload dict.
    """
    cfg = REPORT_CONFIG[report_type]
    market_code = cfg["market"]
    label = cfg["label"]
    date = config.get("date", "")
    url = config["supabase_url"]
    key = config["supabase_key"]

    # 1. 지수·환율 조회
    indices = fetch_latest_indices(url, key, market_code, date)
    fx_rates = fetch_latest_fx(url, key, date)

    # 2. 관심종목 종가 + 섹터
    ticker_infos = fetch_watchlist_tickers(url, key, market_code)
    tickers = [t["ticker"] for t in ticker_infos]
    ticker_names = {t["ticker"]: t["name"] for t in ticker_infos}
    prices = fetch_latest_prices(url, key, tickers, date) if tickers else []
    # daily_prices에 name 컬럼이 없으므로 watchlist에서 가져온 name 병합
    for p in prices:
        p["name"] = ticker_names.get(p["ticker"], p["ticker"])
    # 가격 데이터가 없는 종목도 포함 (name만 표시)
    priced_tickers = {p["ticker"] for p in prices}
    for t in ticker_infos:
        if t["ticker"] not in priced_tickers:
            prices.append({"ticker": t["ticker"], "name": t["name"], "close": 0, "change_pct": 0.0})
    sectors = fetch_company_sectors(url, key, tickers) if tickers else {}

    # 3. Z-score 이상 감지
    anomalies = detect_anomalies_batch(tickers) if tickers else {}

    # 4. ChromaDB 뉴스 검색
    top_news_texts = fetch_top_news(
        chroma_host=config.get("chroma_host", "localhost"),
        chroma_port=config.get("chroma_port", 8001),
        market=market_code,
    )

    # 5. 종목별 뉴스 요약 (첫 번째 검색 결과 스니펫)
    news_summaries = fetch_stock_news_snippets(
        chroma_host=config.get("chroma_host", "localhost"),
        chroma_port=config.get("chroma_port", 8001),
        market=market_code,
        tickers=tickers,
    )

    openai_key = config.get("openai_api_key", "")

    # 6. 종목별 뉴스 LLM 요약
    news_summaries = summarize_stock_news(news_summaries, openai_key=openai_key)

    # 7. LLM 시장 요약
    market_summary = summarize_market_news(
        news_texts=[n["text"] for n in top_news_texts[:5]],
        report_label=label,
        openai_key=openai_key,
    )

    # 8. 주요 뉴스 개별 LLM 요약
    summarized_news = summarize_top_news(top_news_texts[:5], openai_key=openai_key)

    # 9. payload 조립
    market_section = build_market_section(indices, fx_rates)
    stocks_section = build_stocks_section(prices, sectors, anomalies, news_summaries)

    return {
        "market_summary": market_summary,
        "market": market_section,
        "stocks": stocks_section,
        "top_news": summarized_news,
    }


# ── Supabase I/O ─────────────────────────────────────────────────────────


def fetch_latest_indices(supabase_url: str, key: str, market: str, date: str) -> list[dict]:
    """market_indices 테이블에서 해당 market의 최근 지수 데이터를 조회한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        market: "KOR" 또는 "US".
        date: 기준일 (YYYY-MM-DD). 해당일 또는 최근 5일 내 데이터를 반환.

    Returns:
        지수 dict 리스트. 오류 시 빈 리스트.
    """
    from datetime import date as date_cls
    from datetime import timedelta

    try:
        client = create_client(supabase_url, key)
        # 최근 5 영업일 범위로 조회
        start = (date_cls.fromisoformat(date) - timedelta(days=7)).isoformat()
        result = (
            client.table("market_indices")
            .select("*")
            .eq("market", market)
            .gte("date", start)
            .order("date", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        logger.warning("market_indices 조회 실패: market=%s date=%s", market, date, exc_info=True)
        return []


def fetch_latest_fx(supabase_url: str, key: str, date: str) -> list[dict]:
    """fx_rates 테이블에서 최근 환율 데이터를 조회한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        date: 기준일 (YYYY-MM-DD).

    Returns:
        환율 dict 리스트. 오류 시 빈 리스트.
    """
    from datetime import date as date_cls
    from datetime import timedelta

    try:
        client = create_client(supabase_url, key)
        start = (date_cls.fromisoformat(date) - timedelta(days=7)).isoformat()
        result = (
            client.table("fx_rates")
            .select("*")
            .gte("date", start)
            .order("date", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        logger.warning("fx_rates 조회 실패: date=%s", date, exc_info=True)
        return []


def fetch_watchlist_tickers(supabase_url: str, key: str, market: str) -> list[dict]:
    """watchlist 테이블에서 해당 market의 고유 종목 목록을 반환한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        market: "KOR" 또는 "US".

    Returns:
        ticker, name 포함 dict 리스트. 오류 시 빈 리스트.
    """
    try:
        client = create_client(supabase_url, key)
        market_values = _MARKET_VALUES.get(market, [market])
        result = (
            client.table("watchlist").select("ticker, name").in_("market", market_values).execute()
        )
        # 고유 ticker만 추출
        seen: set[str] = set()
        unique: list[dict] = []
        for row in result.data or []:
            if row["ticker"] not in seen:
                seen.add(row["ticker"])
                unique.append({"ticker": row["ticker"], "name": row["name"]})
        return unique
    except Exception:
        logger.warning("watchlist 조회 실패: market=%s", market, exc_info=True)
        return []


def fetch_latest_prices(supabase_url: str, key: str, tickers: list[str], date: str) -> list[dict]:
    """daily_prices 테이블에서 tickers의 최근 종가를 조회한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        tickers: 조회할 종목 티커 리스트.
        date: 기준일 (YYYY-MM-DD).

    Returns:
        ticker, close, change_pct 포함 dict 리스트. 오류 시 빈 리스트.
    """
    from datetime import date as date_cls
    from datetime import timedelta

    if not tickers:
        return []
    try:
        client = create_client(supabase_url, key)
        start = (date_cls.fromisoformat(date) - timedelta(days=7)).isoformat()
        result = (
            client.table("daily_prices")
            .select("ticker, close, change_pct, date")
            .in_("ticker", tickers)
            .gte("date", start)
            .order("date", desc=True)
            .execute()
        )
        # 각 ticker별 최신 row 1개만 추출
        seen: set[str] = set()
        prices: list[dict] = []
        for row in result.data or []:
            if row["ticker"] not in seen:
                seen.add(row["ticker"])
                prices.append(row)
        return prices
    except Exception:
        logger.warning("daily_prices 조회 실패", exc_info=True)
        return []


def fetch_company_sectors(supabase_url: str, key: str, tickers: list[str]) -> dict[str, str]:
    """company_profiles 테이블에서 ticker별 sector를 조회한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        tickers: 조회할 종목 티커 리스트.

    Returns:
        ticker → sector 매핑 dict. 오류 시 빈 dict.
    """
    if not tickers:
        return {}
    try:
        client = create_client(supabase_url, key)
        result = (
            client.table("company_profiles")
            .select("ticker, sector")
            .in_("ticker", tickers)
            .execute()
        )
        return {row["ticker"]: row.get("sector", "") for row in result.data or []}
    except Exception:
        logger.warning("company_profiles 조회 실패", exc_info=True)
        return {}


def get_watchlist_user_ids(supabase_url: str, key: str, market: str) -> list[str]:
    """watchlist에서 해당 market 종목을 가진 사용자 UUID 목록을 반환한다.

    Args:
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.
        market: "KOR" 또는 "US".

    Returns:
        고유 사용자 UUID 리스트. 오류 시 빈 리스트.
    """
    try:
        client = create_client(supabase_url, key)
        market_values = _MARKET_VALUES.get(market, [market])
        result = client.table("watchlist").select("user_id").in_("market", market_values).execute()
        return list({row["user_id"] for row in result.data or []})
    except Exception:
        logger.warning("watchlist user_ids 조회 실패: market=%s", market, exc_info=True)
        return []


def upsert_snapshot(
    report_type: ReportType, date: str, payload: dict, supabase_url: str, key: str
) -> str | None:
    """market_snapshots 테이블에 upsert하고 snapshot id를 반환한다.

    Args:
        report_type: 리포트 타입.
        date: 기준일 (YYYY-MM-DD).
        payload: 리포트 payload dict.
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.

    Returns:
        snapshot UUID 문자열. 오류 시 None.
    """
    try:
        client = create_client(supabase_url, key)
        result = (
            client.table("market_snapshots")
            .upsert(
                {"report_type": report_type, "snapshot_date": date, "payload": payload},
                on_conflict="report_type,snapshot_date",
            )
            .execute()
        )
        if result.data:
            return result.data[0]["id"]
        return None
    except Exception:
        logger.warning(
            "market_snapshots upsert 실패: type=%s date=%s", report_type, date, exc_info=True
        )
        return None


def insert_notifications(
    report_type: ReportType,
    payload: dict,
    user_ids: list[str],
    supabase_url: str,
    key: str,
) -> int:
    """사용자별 notifications 테이블에 알림을 삽입한다.

    Args:
        report_type: 리포트 타입.
        payload: 알림 payload.
        user_ids: 알림을 받을 사용자 UUID 리스트.
        supabase_url: Supabase 프로젝트 URL.
        key: service role key.

    Returns:
        삽입된 알림 수. 오류 시 0.
    """
    if not user_ids:
        return 0
    try:
        client = create_client(supabase_url, key)
        rows = [
            {"user_id": uid, "report_type": report_type, "payload": payload} for uid in user_ids
        ]
        result = client.table("notifications").insert(rows).execute()
        return len(result.data)
    except Exception:
        logger.warning(
            "notifications insert 실패: type=%s users=%d", report_type, len(user_ids), exc_info=True
        )
        return 0


# ── ChromaDB 뉴스 검색 ────────────────────────────────────────────────────


def fetch_top_news(chroma_host: str, chroma_port: int, market: str) -> list[dict]:
    """ChromaDB에서 최신 뉴스 헤드라인을 수집한다.

    Args:
        chroma_host: ChromaDB 호스트.
        chroma_port: ChromaDB 포트.
        market: "KOR" 또는 "US".

    Returns:
        {text, url} dict 리스트. 오류 시 빈 리스트.
    """
    try:
        from app.agent.retriever import get_retriever

        retriever = get_retriever(chroma_host=chroma_host, chroma_port=chroma_port, market=market)
        docs = retriever.invoke("오늘 시장 주요 뉴스" if market == "KOR" else "today market news")
        return [{"text": doc.page_content, "url": doc.metadata.get("url", "")} for doc in docs]
    except Exception:
        logger.warning("ChromaDB 뉴스 조회 실패: market=%s", market, exc_info=True)
        return []


def fetch_stock_news_snippets(
    chroma_host: str,
    chroma_port: int,
    market: str,
    tickers: list[str],
) -> dict[str, str]:
    """종목별 ChromaDB 뉴스 스니펫을 조회한다.

    Args:
        chroma_host: ChromaDB 호스트.
        chroma_port: ChromaDB 포트.
        market: "KOR" 또는 "US".
        tickers: 종목 티커 리스트.

    Returns:
        ticker → {text, url} 매핑 dict. 오류 시 빈 dict.
    """
    if not tickers:
        return {}
    try:
        from app.agent.retriever import get_retriever

        retriever = get_retriever(chroma_host=chroma_host, chroma_port=chroma_port, market=market)
        summaries: dict[str, dict] = {}
        for ticker in tickers:
            try:
                docs = retriever.invoke(ticker)
                if docs:
                    summaries[ticker] = {
                        "text": docs[0].page_content[:300],
                        "url": docs[0].metadata.get("url", ""),
                    }
            except Exception:
                logger.warning("종목 뉴스 스니펫 조회 실패: ticker=%s", ticker)
        return summaries
    except Exception:
        logger.warning("ChromaDB 종목 뉴스 조회 실패: market=%s", market, exc_info=True)
        return {}


# ── LLM 요약 ─────────────────────────────────────────────────────────────


def summarize_market_news(news_texts: list[str], report_label: str, openai_key: str) -> str:
    """OpenAI로 뉴스를 요약하여 market_summary를 생성한다.

    Args:
        news_texts: 뉴스 텍스트 리스트.
        report_label: 리포트 레이블 (예: "한국 장 마감 리포트").
        openai_key: OpenAI API 키.

    Returns:
        요약 문자열. 오류 시 폴백 메시지.
    """
    if not news_texts:
        return f"{report_label}: 오늘의 주요 뉴스를 수집하지 못했습니다."
    try:
        client = OpenAI(api_key=openai_key)
        news_block = "\n".join(f"- {t}" for t in news_texts)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 금융 뉴스 요약 전문가입니다. "
                        "주어진 뉴스를 바탕으로 3~4문장의 핵심 시장 요약을 작성하세요. "
                        "객관적이고 간결하게 작성하며, 투자 권유를 포함하지 마세요."
                    ),
                },
                {
                    "role": "user",
                    "content": f"[{report_label}] 다음 뉴스를 요약해주세요:\n\n{news_block}",
                },
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content or f"{report_label} 요약을 생성했습니다."
    except Exception:
        logger.warning("OpenAI 뉴스 요약 실패", exc_info=True)
        return f"{report_label}: 뉴스 요약을 일시적으로 제공하지 못했습니다."


def summarize_top_news(news_items: list[dict], openai_key: str) -> list[dict]:
    """뉴스 목록을 각각 1~2문장으로 LLM 요약한다.

    Args:
        news_items: {text, url} dict 리스트.
        openai_key: OpenAI API 키.

    Returns:
        {text(요약), url} dict 리스트. 오류 시 원본 반환.
    """
    if not news_items or not openai_key:
        return news_items

    try:
        client = OpenAI(api_key=openai_key)
        numbered = "\n\n".join(f"{i + 1}. {item['text']}" for i, item in enumerate(news_items))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "다음 뉴스 목록을 각각 1~2문장으로 핵심만 요약하세요. "
                        "번호(1. 2. ...)를 그대로 유지하고, 각 요약은 줄바꿈으로 구분하세요. "
                        "투자 권유 없이 객관적으로 작성하세요."
                    ),
                },
                {"role": "user", "content": numbered},
            ],
            max_tokens=400,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        result = []
        for i, item in enumerate(news_items):
            # "1. 요약문" 형태에서 텍스트 추출
            summary = next(
                (line.split(".", 1)[1].strip() for line in lines if line.startswith(f"{i + 1}.")),
                item["text"][:150],
            )
            result.append({"text": summary, "url": item["url"]})
        return result
    except Exception:
        logger.warning("뉴스 개별 요약 실패, 원본 반환", exc_info=True)
        return news_items


def summarize_stock_news(news_summaries: dict[str, dict], openai_key: str) -> dict[str, dict]:
    """종목별 뉴스 스니펫을 각각 1~2문장으로 LLM 요약한다.

    Args:
        news_summaries: ticker → {text, url} 매핑 dict.
        openai_key: OpenAI API 키.

    Returns:
        ticker → {text(요약), url} 매핑 dict. 오류 시 원본 반환.
    """
    if not news_summaries or not openai_key:
        return news_summaries

    tickers = list(news_summaries.keys())
    try:
        client = OpenAI(api_key=openai_key)
        numbered = "\n\n".join(
            f"{i + 1}. [{ticker}] {news_summaries[ticker]['text']}"
            for i, ticker in enumerate(tickers)
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "다음 종목별 뉴스를 각각 1~2문장으로 핵심만 요약하세요. "
                        "번호(1. 2. ...)를 그대로 유지하고, 각 요약은 줄바꿈으로 구분하세요. "
                        "종목명/티커 없이 뉴스 내용만 작성하고, 투자 권유는 포함하지 마세요."
                    ),
                },
                {"role": "user", "content": numbered},
            ],
            max_tokens=100 * len(tickers),
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        result: dict[str, dict] = {}
        for i, ticker in enumerate(tickers):
            original = news_summaries[ticker]
            summary = next(
                (line.split(".", 1)[1].strip() for line in lines if line.startswith(f"{i + 1}.")),
                original["text"][:150],
            )
            result[ticker] = {"text": summary, "url": original["url"]}
        return result
    except Exception:
        logger.warning("종목 뉴스 개별 요약 실패, 원본 반환", exc_info=True)
        return news_summaries


# ── 이상 감지 (배치) ──────────────────────────────────────────────────────


def detect_anomalies_batch(tickers: list[str]) -> dict[str, dict]:
    """여러 종목의 Z-score 이상 감지 결과를 반환한다.

    Args:
        tickers: 종목 티커 리스트.

    Returns:
        ticker → {zscore, is_anomaly} 매핑 dict.
    """
    from app.agent.tools import detect_price_anomaly_json

    results: dict[str, dict] = {}
    for ticker in tickers:
        try:
            data = detect_price_anomaly_json(ticker)
            results[ticker] = {
                "zscore": data.get("zscore"),
                "is_anomaly": data.get("is_anomaly", False),
            }
        except Exception:
            logger.warning("이상 감지 실패: ticker=%s", ticker)
    return results


# ── 파이프라인 통합 실행 ──────────────────────────────────────────────────


def run_report_pipeline(report_type: ReportType, config: dict) -> dict:
    """리포트 파이프라인을 실행한다.

    Args:
        report_type: 리포트 타입.
        config: supabase_url, supabase_key, openai_api_key,
                chroma_host, chroma_port, date 포함 dict.

    Returns:
        report_type, snapshot_id, notifications_inserted, success 포함 dict.
    """
    cfg = REPORT_CONFIG[report_type]
    market_code = cfg["market"]
    url = config["supabase_url"]
    key = config["supabase_key"]
    date = config.get("date", "")

    try:
        # 1. payload 빌드
        payload = build_payload(report_type, config)

        # 2. market_snapshots upsert
        snapshot_id = upsert_snapshot(report_type, date, payload, url, key)

        # 3. 사용자 조회 & 알림 삽입
        user_ids = get_watchlist_user_ids(url, key, market_code)
        notifications_inserted = 0
        if user_ids:
            notifications_inserted = insert_notifications(report_type, payload, user_ids, url, key)

        return {
            "report_type": report_type,
            "snapshot_id": snapshot_id,
            "notifications_inserted": notifications_inserted,
            "success": True,
        }

    except Exception as exc:
        logger.error("리포트 파이프라인 실패: type=%s error=%s", report_type, exc, exc_info=True)
        return {
            "report_type": report_type,
            "snapshot_id": None,
            "notifications_inserted": 0,
            "success": False,
            "error": str(exc),
        }
