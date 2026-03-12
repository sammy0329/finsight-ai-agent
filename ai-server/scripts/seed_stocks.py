"""
종목 목록을 Supabase stocks 테이블에 적재하는 시드 스크립트.

실행:
    cd ai-server
    poetry run python scripts/seed_stocks.py
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

import FinanceDataReader as fdr
import requests
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.error("환경변수 SUPABASE_URL, SUPABASE_SERVICE_KEY 를 설정하세요")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def fetch_krx_listing(mkt_id: str) -> list[dict]:
    """KRX OPEN API 직접 호출 (Referer 헤더 포함)"""
    today = datetime.now().strftime("%Y%m%d")
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    headers = {
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiBoardDetail/MDCSTAT01501",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "locale": "ko_KR",
        "mktId": mkt_id,  # STK=KOSPI, KSQ=KOSDAQ
        "trdDd": today,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
    }
    try:
        res = requests.post(url, headers=headers, data=data, timeout=10)
        res.raise_for_status()
        return res.json().get("OutBlock_1", [])
    except Exception as e:
        logger.warning(f"KRX API 호출 실패 ({mkt_id}): {e}")
        return []


def seed_krx():
    """KRX OPEN API로 실시간 종목 목록 적재, 실패 시 주요 종목 하드코딩"""
    # KRX API 시도
    stocks = []
    for mkt_id, market in [("STK", "KOSPI"), ("KSQ", "KOSDAQ")]:
        logger.info(f"{market} 종목 목록 수집 중 (KRX API)...")
        rows = fetch_krx_listing(mkt_id)
        if rows:
            for row in rows:
                ticker = str(row.get("ISU_SRT_CD", "")).strip()
                name = str(row.get("ISU_ABBRV", "")).strip()
                if ticker and name:
                    stocks.append({"ticker": ticker, "name": name, "market": market})
            logger.info(f"  {market}: {len([s for s in stocks if s['market'] == market])}개")

    if stocks:
        seen = set()
        unique = [s for s in stocks if not (s["ticker"] in seen or seen.add(s["ticker"]))]
        logger.info(f"KRX 전체: {len(unique)}개")
        _upsert_batch(unique)
        return len(unique)

    # API 실패 시 주요 종목 fallback
    logger.warning("KRX API 실패 — 주요 종목 fallback 사용")
    kospi = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("005380", "현대차"),
        ("035420", "NAVER"),
        ("005490", "POSCO홀딩스"),
        ("000270", "기아"),
        ("068270", "셀트리온"),
        ("105560", "KB금융"),
        ("055550", "신한지주"),
        ("012330", "현대모비스"),
        ("028260", "삼성물산"),
        ("066570", "LG전자"),
        ("096770", "SK이노베이션"),
        ("003550", "LG"),
        ("032830", "삼성생명"),
        ("017670", "SK텔레콤"),
        ("030200", "KT"),
        ("086790", "하나금융지주"),
        ("003490", "대한항공"),
        ("009150", "삼성전기"),
        ("018260", "삼성에스디에스"),
        ("010950", "S-Oil"),
        ("011170", "롯데케미칼"),
        ("034730", "SK"),
        ("316140", "우리금융지주"),
        ("033780", "KT&G"),
        ("015760", "한국전력"),
        ("035720", "카카오"),
        ("259960", "크래프톤"),
        ("047050", "포스코인터내셔널"),
        ("006400", "삼성SDI"),
        ("051910", "LG화학"),
        ("207940", "삼성바이오로직스"),
        ("000720", "현대건설"),
        ("002790", "아모레퍼시픽그룹"),
        ("161390", "한국타이어앤테크놀로지"),
        ("003670", "포스코퓨처엠"),
        ("373220", "LG에너지솔루션"),
        ("247540", "에코프로비엠"),
        ("086280", "현대글로비스"),
        ("009830", "한화솔루션"),
        ("000810", "삼성화재"),
        ("021240", "코웨이"),
        ("138040", "메리츠금융지주"),
        ("402340", "SK스퀘어"),
        ("010140", "삼성중공업"),
        ("010130", "고려아연"),
        ("011790", "SKC"),
        ("029780", "삼성카드"),
        ("018880", "한온시스템"),
    ]
    kosdaq = [
        ("042700", "한미반도체"),
        ("058470", "리노공업"),
        ("263750", "펄어비스"),
        ("112040", "위메이드"),
        ("357780", "솔브레인"),
        ("196170", "알테오젠"),
        ("145020", "휴젤"),
        ("028300", "HLB"),
        ("064350", "현대로템"),
        ("293490", "카카오게임즈"),
        ("036570", "엔씨소프트"),
        ("251270", "넷마블"),
        ("035900", "JYP Ent."),
        ("041510", "에스엠"),
        ("122870", "와이지엔터테인먼트"),
        ("039030", "이오테크닉스"),
        ("086520", "에코프로"),
        ("091990", "셀트리온헬스케어"),
        ("214150", "클래시스"),
    ]

    seen = set()
    stocks = []
    for code, name in kospi:
        if code not in seen:
            seen.add(code)
            stocks.append({"ticker": code, "name": name, "market": "KOSPI"})
    for code, name in kosdaq:
        if code not in seen:
            seen.add(code)
            stocks.append({"ticker": code, "name": name, "market": "KOSDAQ"})

    logger.info(f"KRX 주요 종목: KOSPI {len(kospi)}개, KOSDAQ {len(kosdaq)}개")
    _upsert_batch(stocks)
    return len(stocks)


def seed_sp500():
    logger.info("S&P500 종목 목록 수집 중...")
    df = fdr.StockListing("S&P500")

    col_code = next((c for c in ["Symbol", "Code"] if c in df.columns), None)
    col_name = next((c for c in ["Name", "Security", "ShortName"] if c in df.columns), None)

    if not col_code or not col_name:
        logger.error(f"컬럼을 찾을 수 없음: {df.columns.tolist()}")
        return 0

    stocks = []
    for _, row in df.iterrows():
        ticker = str(row[col_code]).strip()
        name = str(row[col_name]).strip()
        if not ticker or not name:
            continue
        stocks.append({"ticker": ticker, "name": name, "market": "S&P500"})

    logger.info(f"S&P500 종목 수: {len(stocks)}")
    _upsert_batch(stocks)
    return len(stocks)


def _upsert_batch(stocks: list[dict], batch_size: int = 500):
    """Supabase에 배치 upsert"""
    total = 0
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i : i + batch_size]
        supabase.table("stocks").upsert(batch, on_conflict="ticker").execute()
        total += len(batch)
        logger.info(f"  적재: {total}/{len(stocks)}")


def seed_prices():
    """stocks 테이블의 모든 종목 전일 종가 수집 → daily_prices 적재"""
    # 적재된 종목 목록 조회
    res = supabase.table("stocks").select("ticker, market").execute()
    all_stocks = res.data or []
    logger.info(f"\n가격 수집 시작 — 총 {len(all_stocks)}개 종목")

    # 최근 5 영업일 범위 (주말/공휴일 대응)
    end = datetime.now()
    start = end - timedelta(days=7)
    start_str = start.strftime("%Y-%m-%d")

    prices = []
    failed = 0

    for i, stock in enumerate(all_stocks):
        ticker = stock["ticker"]
        market = stock["market"]
        # 점 표기 변환 (BRKB→BRK.B, BFB→BF.B 등 Yahoo Finance 호환)
        ticker_map = {"BRKB": "BRK.B", "BFB": "BF.B"}
        fdr_ticker = ticker_map.get(ticker, ticker)

        try:
            df = fdr.DataReader(fdr_ticker, start_str)
            if df.empty:
                failed += 1
                continue

            # 가장 최근 거래일 데이터
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else None

            close = float(latest["Close"])
            if prev is not None and float(prev["Close"]) > 0:
                change_pct = round((close - float(prev["Close"])) / float(prev["Close"]) * 100, 2)
            else:
                change_pct = 0.0

            date_str = df.index[-1].strftime("%Y-%m-%d")
            prices.append(
                {
                    "ticker": ticker,
                    "date": date_str,
                    "close": close,
                    "change_pct": change_pct,
                }
            )

        except Exception as e:
            logger.warning(f"  실패 [{ticker}] {market}: {e}")
            failed += 1

        # 진행률 표시 + rate limit 방지
        if (i + 1) % 50 == 0:
            logger.info(f"  진행: {i + 1}/{len(all_stocks)} (실패: {failed})")
            time.sleep(1)

    logger.info(f"가격 수집 완료 — 성공: {len(prices)}개, 실패: {failed}개")

    # daily_prices upsert
    for i in range(0, len(prices), 200):
        batch = prices[i : i + 200]
        supabase.table("daily_prices").upsert(batch, on_conflict="ticker,date").execute()
        logger.info(f"  가격 적재: {min(i + 200, len(prices))}/{len(prices)}")

    return len(prices)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--prices-only", action="store_true", help="가격만 업데이트")
    args = parser.parse_args()

    if args.prices_only:
        seed_prices()
    else:
        krx_count = seed_krx()
        sp500_count = seed_sp500()
        logger.info(f"\n종목 목록 완료 — KRX: {krx_count}개, S&P500: {sp500_count}개")
        seed_prices()
