"""T-104: FinanceDataReader 국내 주가 수집 모듈.

KOSPI/KOSDAQ 주요 종목의 일별 OHLCV 데이터를 수집한다.
외부 라이브러리 FinanceDataReader를 사용하며, 오류 발생 시 빈 리스트를 반환하여
파이프라인이 중단되지 않도록 한다.
"""

import logging

import FinanceDataReader as fdr

logger = logging.getLogger(__name__)


def fetch_stock_data(
    tickers: list[str],
    start_date: str,
    end_date: str,
) -> list[dict]:
    """주어진 종목 코드 리스트에 대해 일별 OHLCV 데이터를 수집한다.

    Args:
        tickers: 종목 코드 리스트 (예: ["005930", "000660"])
        start_date: 조회 시작일 (YYYY-MM-DD)
        end_date: 조회 종료일 (YYYY-MM-DD)

    Returns:
        OHLCV dict 리스트. 오류 발생 시 빈 리스트 반환.
    """
    if not tickers:
        return []

    results: list[dict] = []

    for ticker in tickers:
        try:
            df = fdr.DataReader(ticker, start_date, end_date)
            if df.empty:
                continue

            for date_idx, row in df.iterrows():
                results.append(
                    {
                        "ticker": ticker,
                        "date": date_idx.strftime("%Y-%m-%d"),
                        "open": row["Open"],
                        "high": row["High"],
                        "low": row["Low"],
                        "close": row["Close"],
                        "volume": row["Volume"],
                    }
                )
        except Exception:
            logger.warning("Failed to fetch data for ticker=%s", ticker, exc_info=True)
            continue

    return results
