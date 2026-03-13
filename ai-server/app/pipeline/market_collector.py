"""T-603/T-604: 시장 지수 및 환율 수집 모듈.

FinanceDataReader를 사용하여 주요 지수(KOSPI, KOSDAQ, S&P500, NASDAQ, DOW)와
환율(USD/KRW, EUR/KRW)을 수집한다.
오류 발생 시 빈 리스트를 반환하여 파이프라인이 중단되지 않도록 한다.
"""

import logging
from datetime import datetime, timedelta

import FinanceDataReader as fdr

logger = logging.getLogger(__name__)

INDICES: list[tuple[str, str, str]] = [
    ("^KS11", "KOSPI", "KOR"),
    ("^KQ11", "KOSDAQ", "KOR"),
    ("^GSPC", "S&P500", "US"),
    ("^IXIC", "NASDAQ", "US"),
    ("^DJI", "DOW", "US"),
]

FX_PAIRS: list[str] = ["USD/KRW", "EUR/KRW"]


def fetch_market_indices(date: str, *, market: str = "KOR") -> list[dict]:
    """주요 시장 지수를 수집한다.

    Args:
        date: 조회 기준일 (YYYY-MM-DD)
        market: "KOR" 또는 "US"

    Returns:
        지수 dict 리스트. 오류 시 빈 리스트.
    """
    results: list[dict] = []
    target_indices = [(s, n, m) for s, n, m in INDICES if m == market]

    # 전일 대비 등락률 계산을 위해 최근 5거래일 조회
    lookback = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    for symbol, name, mkt in target_indices:
        try:
            df = fdr.DataReader(symbol, lookback, date)
            if df.empty or len(df) < 1:
                continue

            close_today = float(df["Close"].iloc[-1])
            if len(df) >= 2:
                close_prev = float(df["Close"].iloc[-2])
                change_pct = round((close_today - close_prev) / close_prev * 100, 2)
            else:
                change_pct = 0.0

            results.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "date": date,
                    "close": close_today,
                    "change_pct": change_pct,
                    "market": mkt,
                }
            )
        except Exception:
            logger.warning("지수 수집 실패: symbol=%s", symbol, exc_info=True)
            continue

    return results


def fetch_fx_rates(date: str) -> list[dict]:
    """환율 데이터를 수집한다.

    Args:
        date: 조회 기준일 (YYYY-MM-DD)

    Returns:
        환율 dict 리스트. 오류 시 빈 리스트.
    """
    results: list[dict] = []

    for pair in FX_PAIRS:
        try:
            df = fdr.DataReader(pair, date, date)
            if df.empty:
                continue

            row = df.iloc[-1]
            results.append(
                {
                    "pair": pair,
                    "date": date,
                    "rate": float(row["Close"]),
                }
            )
        except Exception:
            logger.warning("환율 수집 실패: pair=%s", pair, exc_info=True)
            continue

    return results
