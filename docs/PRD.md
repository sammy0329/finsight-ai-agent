# 제품 요구사항 정의서 (PRD)

**프로젝트명:** 고객 세그먼트 기반 맞춤형 투자 인사이트 AI 에이전트 (FinSight Agent)

**목표:** 뉴스·공시·실시간 가격 데이터를 다중 도구(Multi-tool)로 연계하는 LangChain 에이전트를 구축하고, 사용자 투자 성향(세그먼트)에 따라 검색 전략과 답변 관점을 동시에 분기하는 MSA 기반 개인화 투자 인사이트 서비스 구현.

---

### 1. 프로젝트 배경 및 비즈니스 목표

- **배경:** 넘쳐나는 금융 정보 속에서 고객은 자신의 투자 성향에 맞는 유의미한 정보를 찾기 어려워함. 초개인화된 자산 관리 서비스의 필요성 대두.
- **비즈니스 목표:** 고객 세그멘테이션에 따른 맞춤형 정보 제공으로 고객 인게이지먼트 향상 및 증권사 플랫폼 체류 시간 증대.
- **기술적 목표:**
  - 단순 RAG 래퍼를 넘어 **Agent가 질문 유형에 따라 필요한 데이터 소스를 스스로 선택**하는 Multi-tool 구조 구현
  - 뉴스(ChromaDB), 공시(DART API), 가격(Yahoo Finance) 세 가지 이질적 데이터를 하나의 답변으로 종합
  - 가격 이상 감지(통계 기반)와 AI 설명을 자동 연계하는 데이터 기반 트리거 구현
  - Next.js + FastAPI + Supabase 마이크로서비스 연계 및 Vercel·EC2 배포

---

### 2. 타겟 유저 (고객 세그먼트)

에이전트가 **검색 전략(필터)과 프롬프트(어조)를 동시에 분기**하는 기준이 되는 3가지 투자 성향 페르소나.

| 세그먼트 | 특성 | 관심 자산군 | 검색 전략 | 프롬프트 어조 |
|---|---|---|---|---|
| **안전추구형 (A형)** | 원금 손실을 극도로 꺼리며 안정적 수익 우선 | 배당주, 우량주, 국채 | 리스크·배당 뉴스 우선 | 보수적, 리스크 중심 |
| **위험감수형 (B형)** | 높은 변동성을 감수, 시장 초과 수익 지향 | 성장주, 테마주, 단기 모멘텀 | 가격 이상·급등락 뉴스 우선 | 공격적, 기회 중심 |
| **가치투자형 (C형)** | 펀더멘털·장기 산업 전망 기반 우량주 투자 | 실적주, 저PER, 산업 대표주 | 공시·실적 문서 우선 | 분석적, 장기 관점 |

---

### 3. 핵심 요구사항 (Functional Requirements)

| 요구사항 ID | 기능명 | 설명 | 담당 시스템 |
|---|---|---|---|
| **FR-01** | **사용자 프로필 관리** | 투자 성향(A/B/C), 관심종목 watchlist 데이터 저장·관리 | Next.js + Supabase |
| **FR-02** | **금융 데이터 파이프라인** | 매일 장 마감 후(16:30 KST) 뉴스·공시 자동 수집·벡터화·ChromaDB 적재 | Python + GitHub Actions |
| **FR-03** | **데이터 정제 및 벡터화** | 수집 텍스트 청킹·임베딩, 메타데이터(ticker·category·source) 부착 후 ChromaDB upsert | Python + LangChain |
| **FR-04** | **실시간 가격 연동** | Yahoo Finance API로 관심종목 실시간 종가·등락률, KOSPI/NASDAQ/환율 시장 요약 제공 | Next.js (lib/yahoo.ts) |
| **FR-05** | **가격 이상 감지** | 최근 N일 표준편차 대비 당일 변동폭 Z-score 산출 → 이상 감지 시 자동 인사이트 트리거 | FastAPI (price_anomaly tool) |
| **FR-06** | **Multi-tool AI 에이전트** | Agent가 질문 유형 판단 → 필요한 도구(뉴스 검색 / 공시 조회 / 가격 분석)를 선택·실행·종합 | FastAPI + LangChain AgentExecutor |
| **FR-07** | **세그먼트 기반 개인화** | 사용자 세그먼트에 따라 검색 메타데이터 필터와 시스템 프롬프트를 동시 분기 | FastAPI Agent |
| **FR-08** | **인사이트 스트리밍** | Agent 추론 과정 및 최종 답변을 SSE 스트리밍으로 실시간 전달 | FastAPI → Next.js → Client |
| **FR-09** | **이력 저장 및 조회** | 인사이트 요청·답변·출처를 Supabase에 저장, 날짜별 이력 페이지 제공 | Supabase + Next.js |

---

### 4. 비기능 요구사항 (Non-Functional Requirements)

| 항목 | 요구사항 | 비고 |
|---|---|---|
| **응답 시간** | AI 인사이트 응답 P95 < 5초 | SSE 스트리밍으로 체감 지연 최소화 |
| **데이터 신선도** | 매일 16:30 이전 ChromaDB 업데이트 완료 | 파이프라인 실패 시 전날 데이터로 폴백 |
| **가용성** | 파이프라인 실패 시 Slack 알림 및 자동 재시도 | GitHub Actions 최대 2회 재실행 |
| **확장성** | 도구(Tool)·세그먼트 타입을 코드 변경 없이 추가 가능 | Config-driven Agent 구조 |
| **보안** | API Key 및 민감 정보는 환경변수·Secret Manager 관리 | 코드베이스 하드코딩 금지 |
| **투자 면책** | 모든 답변 하단에 비투자권유 고지문 포함 | 자본시장법 준수 |

---

### 5. 데이터 소스 및 수집 명세 (FR-02 상세)

| 데이터 유형 | 소스 | API / 라이브러리 | 수집 주기 | Agent 도구 |
|---|---|---|---|---|
| 국내 금융 뉴스 | 네이버 뉴스 | Naver Search API | 일 1회 (파이프라인) | search_news_tool |
| 미국 금융 뉴스 | NewsAPI | REST API | 일 1회 (파이프라인) | search_news_tool |
| 국내 기업 공시 | 금융감독원 DART | OpenDart REST API | 일 1회 (파이프라인) + 온디맨드 | get_dart_tool |
| 실시간 주가·시장 | Yahoo Finance | query1.finance.yahoo.com | 온디맨드 (캐시 30~60분) | get_price_tool |
| 국내 주가 이력 | FinanceDataReader | `fdr.DataReader()` | 일 1회 (가격 이상 감지용) | price_anomaly_tool |

---

### 6. Agent 도구 설계 (FR-06 상세)

Agent는 유저 질문을 분석하여 아래 4개 도구 중 필요한 것을 선택·조합하여 실행합니다.

```
유저: "삼성전자 오늘 왜 이렇게 떨어졌어?"

Agent 판단:
  1. get_price_tool("005930")       → 오늘 -2.8% 확인, Z-score 3.1 (이상)
  2. search_news_tool("삼성전자")   → 관련 뉴스 Top-5 청크 검색
  3. get_dart_tool("005930")        → 최근 30일 주요 공시 확인

→ 세 결과를 세그먼트 B형 관점으로 종합하여 답변 생성
```

| 도구명 | 입력 | 출처 | 설명 |
|---|---|---|---|
| `search_news_tool` | 키워드, market, category | ChromaDB (RAG) | 뉴스·공시 벡터 검색, 세그먼트별 메타데이터 필터 적용 |
| `get_dart_tool` | 종목코드 | DART OpenAPI | 최근 30일 공시 목록 조회 및 핵심 내용 요약 |
| `get_price_tool` | ticker, market | Yahoo Finance | 현재 종가·등락률·거래량 조회 |
| `price_anomaly_tool` | ticker, market | FinanceDataReader + 통계 | 최근 20일 기준 Z-score 산출, 이상 여부 판정 |

---

### 7. 데이터 구조 및 Vector DB 스키마 (FR-03 상세)

수집된 비정형 텍스트는 아래 구조로 청킹·메타데이터 부착 후 ChromaDB에 적재합니다.

```json
{
  "document": "삼성전자, 2분기 영업이익 10조 돌파... HBM 수요 급증에 반도체 부문 흑자 전환",
  "metadata": {
    "source": "naver_news | dart | newsapi",
    "published_at": "2025-03-10T14:30:00",
    "collected_at": "2025-03-10T16:35:00",
    "market": "KOR | US",
    "related_tickers": ["005930", "000660"],
    "category": "semiconductor | macro | energy | bio_pharma",
    "sentiment": "positive | negative | neutral"
  }
}
```

**청킹 전략:**
- 뉴스 1건당 최대 500 토큰 분할, 50 토큰 오버랩
- 공시 데이터는 섹션(사업 개요·재무 현황·주요 사항) 기준 분할
- 청크 경계는 문장 단위로 처리하여 의미 단절 방지

---

### 8. 시스템 아키텍처

**Frontend & BFF (Next.js / Vercel)**
- 사용자 인증(Supabase Auth), 관심종목 관리, 실시간 가격 표시, Agent API 프록시

**AI & Data Backend (FastAPI / EC2)**
- LangChain AgentExecutor 기반 Multi-tool 에이전트
- 도구 선택 → 실행 → 결과 종합 → 세그먼트 프롬프트 적용 → SSE 스트리밍

**Data Pipeline (GitHub Actions)**
- 평일 16:30 KST 자동 실행: 수집 → 정제 → 임베딩 → ChromaDB 적재
- 실패 시 Slack 알림 + 최대 2회 재시도

---

### 9. 주요 API 연계 흐름 (Multi-tool Agent Sequence)

1. **Client:** `/insight/005930` 페이지에서 "삼성전자 오늘 왜 떨어졌어?" 요청
2. **Next.js API Route (`/api/insight`):** Supabase에서 사용자 세그먼트 `B` (위험감수형) 조회
3. **Next.js → FastAPI:** `POST /api/ai/insight/stream` 호출
   ```json
   { "user_segment": "B", "ticker": "005930", "query": "삼성전자 오늘 왜 이렇게 떨어졌어?" }
   ```
4. **FastAPI Agent:**
   - `get_price_tool` → 오늘 -2.8%, Z-score 3.1 (이상 감지)
   - `search_news_tool` → 관련 뉴스 Top-5 검색 (category=semiconductor 필터)
   - `get_dart_tool` → 최근 공시 확인
5. **FastAPI → LLM:** B형 시스템 프롬프트 + 3개 도구 결과 컨텍스트 → 인사이트 생성
6. **FastAPI → Next.js → Client:** SSE 스트리밍 전달
7. **Next.js:** `insight_history` 테이블에 이력 저장 (도구별 출처 포함)

---

### 10. AI 에이전트 품질 평가 기준

단순 구현을 넘어 에이전트 답변 품질을 측정하고 개선하기 위한 평가 지표를 정의합니다.

| 평가 항목 | 측정 방법 | 목표 기준 |
|---|---|---|
| **Retrieval 품질** | 질의 관련 청크가 Top-5 내 포함되는 비율 (Recall@5) | ≥ 80% |
| **도구 선택 정확도** | 질문 유형별 적절한 도구가 호출되는 비율 (수동 평가 30건) | ≥ 85% |
| **세그먼트 적합성** | A/B/C 답변이 실제로 상이한지 정성 평가 (샘플 10건) | 평가자 일치율 ≥ 70% |
| **환각(Hallucination) 비율** | 검색된 청크에 없는 정보를 답변에 포함하는 비율 | ≤ 10% |
| **응답 완결성** | 핵심 포인트(시황 요약·리스크·관련 종목)를 모두 포함하는 비율 | ≥ 90% |

---

### 11. 구현 로드맵 (마일스톤)

| Phase | 목표 | 주요 산출물 |
|---|---|---|
| **Phase 1** | 데이터 파이프라인 구축 | 뉴스·공시 수집 → 벡터화 자동화, ChromaDB 적재 확인 |
| **Phase 2** | Multi-tool AI 에이전트 구현 | AgentExecutor + 4개 도구, 세그먼트 분기, 스트리밍 |
| **Phase 3** | Next.js + Supabase 프론트엔드 | 인증·watchlist·실시간 가격·인사이트 UI, Vercel 배포 |
| **Phase 4** | 품질 평가 및 최적화 | Recall@5·도구 선택 정확도 측정, 파라미터 튜닝, 최종 문서화 |
