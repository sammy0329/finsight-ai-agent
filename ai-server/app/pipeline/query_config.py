"""T-121: 데이터 파이프라인 수집 쿼리 설정.

카테고리별 세분화된 뉴스 수집 쿼리를 정의한다.
"""

KOR_QUERIES: list[dict] = [
    {"category": "macro", "query": "금리 통화정책 한국은행"},
    {"category": "stock_market", "query": "코스피 코스닥 증시"},
    {"category": "semiconductor", "query": "반도체 삼성전자 SK하이닉스"},
    {"category": "exchange_rate", "query": "환율 원달러 외환"},
    {"category": "energy", "query": "유가 에너지 원자재"},
    {"category": "bio_pharma", "query": "바이오 제약 신약"},
    {"category": "real_estate", "query": "부동산 건설 PF"},
    {"category": "crypto", "query": "비트코인 가상자산 암호화폐"},
]

US_QUERIES: list[dict] = [
    {
        "category": "macro",
        "query": "Federal Reserve interest rate monetary policy",
        "page_size": 15,
    },
    {"category": "stock_market", "query": "S&P 500 Wall Street stock market", "page_size": 15},
    {"category": "semiconductor", "query": "semiconductor chip NVIDIA AI", "page_size": 15},
    {"category": "energy", "query": "oil price energy crude", "page_size": 15},
    {"category": "big_tech", "query": "Apple Google Microsoft earnings", "page_size": 15},
    {"category": "crypto", "query": "Bitcoin cryptocurrency digital asset", "page_size": 15},
]
