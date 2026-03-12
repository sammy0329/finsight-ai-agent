# 제품 요구사항 정의서 (PRD)

**프로젝트명:** 고객 세그먼트 기반 맞춤형 투자 인사이트 AI 에이전트 (FinSight Agent)

**목표:** 뉴스·공시·실시간 가격·재무 데이터를 다중 도구(Multi-tool)로 연계하는 LangChain 에이전트를 구축하고, 사용자 투자 성향(세그먼트)에 따라 검색 전략과 답변 관점을 동시에 분기하며, 장 시작 전 모닝 브리프를 자동 발송하는 MSA 기반 개인화 투자 인사이트 서비스 구현.

---

### 1. 프로젝트 배경 및 비즈니스 목표

- **배경:** 넘쳐나는 금융 정보 속에서 고객은 자신의 투자 성향에 맞는 유의미한 정보를 찾기 어려워함. 초개인화된 자산 관리 서비스의 필요성 대두.
- **비즈니스 목표:** 고객 세그멘테이션에 따른 맞춤형 정보 제공으로 고객 인게이지먼트 향상 및 증권사 플랫폼 체류 시간 증대.
- **기술적 목표:**
  - 단순 RAG 래퍼를 넘어 **Agent가 질문 유형에 따라 필요한 데이터 소스를 스스로 선택**하는 Multi-tool 구조 구현
  - 뉴스(ChromaDB), 공시(DART API), 가격(Yahoo Finance), 재무지표(Supabase) 네 가지 이질적 데이터를 하나의 답변으로 종합
  - 가격 이상 감지(통계 기반)와 AI 설명을 자동 연계하는 데이터 기반 트리거 구현
  - **한국/미국 장전·장마감 4종 리포트를 자동 생성하여 인앱 알림으로 전달** (GitHub Actions + Supabase)
  - Next.js + FastAPI + Supabase 마이크로서비스 연계 및 Vercel·EC2 배포

---

### 2. 타겟 유저 (고객 세그먼트)

에이전트가 **검색 전략(필터)과 프롬프트(어조)를 동시에 분기**하는 기준이 되는 3가지 투자 성향 페르소나.

| 세그먼트 | 특성 | 관심 자산군 | 검색 전략 | 프롬프트 어조 |
|---|---|---|---|---|
| **안전추구형 (A형)** | 원금 손실을 극도로 꺼리며 안정적 수익 우선 | 배당주, 우량주, 국채 | 리스크·배당 뉴스 우선 | 보수적, 리스크 중심 |
| **위험감수형 (B형)** | 높은 변동성을 감수, 시장 초과 수익 지향 | 성장주, 테마주, 단기 모멘텀 | 가격 이상·급등락 뉴스 우선 | 공격적, 기회 중심 |
| **가치투자형 (C형)** | 펀더멘털·장기 산업 전망 기반 우량주 투자 | 실적주, 저PER, 산업 대표주 | 공시·실적·재무 문서 우선 | 분석적, 장기 관점 |

---

### 3. 핵심 요구사항 (Functional Requirements)

| 요구사항 ID | 기능명 | 설명 | 담당 시스템 | 상태 |
|---|---|---|---|---|
| **FR-01** | **사용자 프로필 관리** | 투자 성향(A/B/C), 관심종목 watchlist 데이터 저장·관리 | Next.js + Supabase | ✅ |
| **FR-02** | **금융 데이터 파이프라인** | 매일 장 마감 후(16:30 KST) 뉴스·공시 자동 수집·벡터화·ChromaDB 적재 | Python + GitHub Actions | ✅ |
| **FR-03** | **데이터 정제 및 벡터화** | 수집 텍스트 청킹·임베딩, 메타데이터 부착 후 ChromaDB upsert | Python + LangChain | ✅ |
| **FR-04** | **실시간 가격 연동** | Yahoo Finance API로 관심종목 실시간 종가·등락률, 시장 요약 제공 | Next.js (lib/yahoo.ts) | ✅ |
| **FR-05** | **가격 이상 감지** | 최근 20일 Z-score 산출 → 이상 감지 시 자동 인사이트 트리거 | FastAPI (price_anomaly_tool) | ✅ |
| **FR-06** | **Multi-tool AI 에이전트** | Agent가 질문 유형 판단 → 필요한 도구를 선택·실행·종합 | FastAPI + LangChain AgentExecutor | ✅ |
| **FR-07** | **세그먼트 기반 개인화** | 사용자 세그먼트에 따라 검색 필터와 시스템 프롬프트를 동시 분기 | FastAPI Agent | ✅ |
| **FR-08** | **인사이트 스트리밍** | Agent 답변을 SSE 스트리밍으로 실시간 전달 | FastAPI → Next.js → Client | ✅ |
| **FR-09** | **이력 저장 및 조회** | 인사이트 요청·답변·출처를 Supabase에 저장, 날짜별 이력 제공 | Supabase + Next.js | ✅ |
| **FR-10** | **재무 데이터 통합** | 분기별 PER·PBR·ROE·매출·영업이익 Supabase 적재, `get_financials_tool` 연동 | DART API + Supabase | ✅ |
| **FR-11** | **리포트 시스템 자동 발송 (4종)** | 한국/미국 장전·장마감 4종 리포트 자동 생성 → 인앱 알림 (08:00·16:30·22:30·07:00 KST) | GitHub Actions + Supabase | 🔲 |

---

### 4. 비기능 요구사항 (Non-Functional Requirements)

| 항목 | 요구사항 | 비고 |
|---|---|---|
| **응답 시간** | AI 인사이트 응답 P95 < 5초 | SSE 스트리밍으로 체감 지연 최소화 |
| **데이터 신선도** | 매일 16:30 이전 ChromaDB 업데이트 완료 | 파이프라인 실패 시 전날 데이터로 폴백 |
| **리포트 발송** | 4종 리포트 각 스케줄 ± 5분 (08:00, 16:30, 22:30, 07:00 KST) | GitHub Actions cron 기반 |
| **가용성** | 파이프라인 실패 시 Slack 알림 및 자동 재시도 | GitHub Actions 최대 2회 재실행 |
| **확장성** | 도구(Tool)·세그먼트 타입을 코드 변경 없이 추가 가능 | Config-driven Agent 구조 |
| **보안** | API Key 및 민감 정보는 환경변수·Secret Manager 관리 | 코드베이스 하드코딩 금지 |
| **투자 면책** | 모든 답변 하단에 비투자권유 고지문 포함 | 자본시장법 준수 |

---

### 5. 데이터 소스 및 수집 명세

| 데이터 유형 | 소스 | API / 라이브러리 | 수집 주기 | Agent 도구 |
|---|---|---|---|---|
| 국내 금융 뉴스 | 네이버 뉴스 | Naver Search API | 일 1회 (파이프라인) | search_news_tool |
| 미국 금융 뉴스 | NewsAPI | REST API | 일 1회 (파이프라인) | search_news_tool |
| 국내 기업 공시 | 금융감독원 DART | OpenDart REST API | 일 1회 + 온디맨드 | get_dart_tool |
| 실시간 주가·시장 | Yahoo Finance | query1.finance.yahoo.com | 온디맨드 (캐시 30~60분) | get_price_tool |
| 국내 주가 이력 | FinanceDataReader | `fdr.DataReader()` | 온디맨드 (이상 감지용) | price_anomaly_tool |
| **분기 재무지표** | **DART 재무제표 API** | `fnlttSinglAcnt` | **분기 1회** | **get_financials_tool** |
| **기업 개요** | **DART 기업개황 API** | `company.json` | **연 1회** | **get_financials_tool** |

---

### 6. Agent 도구 설계 (FR-06 상세)

Agent는 유저 질문을 분석하여 아래 5개 도구 중 필요한 것을 선택·조합하여 실행합니다.

```
유저: "삼성전자 PBR이 낮은데 지금 저평가인가요?" (C형 — 가치투자형)

Agent 판단:
  1. get_financials_tool("005930")  → PER 12.3, PBR 1.1, ROE 8.2% (Supabase)
  2. search_news_tool("삼성전자")   → 관련 뉴스 Top-5 (ChromaDB RAG)
  3. get_dart_tool("삼성전자")      → 최근 분기 실적 공시 확인

→ 세 결과를 C형 관점(펀더멘털 분석)으로 종합하여 답변 생성
```

| 도구명 | 입력 | 출처 | 설명 |
|---|---|---|---|
| `search_news_tool` | 키워드, market | ChromaDB (RAG) | 뉴스·공시 벡터 검색 |
| `get_dart_tool` | 기업명 | DART OpenAPI | 최근 30일 공시 목록 조회 |
| `get_price_tool` | ticker | Yahoo Finance | 현재 종가·등락률 조회 |
| `price_anomaly_tool` | ticker | FinanceDataReader + 통계 | Z-score 이상 감지 |
| `get_financials_tool` | ticker | Supabase financial_metrics | PER, PBR, ROE, 매출, 영업이익 조회 |

---

### 7. 재무 데이터 설계 (FR-10 상세)

**Supabase 스키마:**
```sql
-- 분기별 재무지표
create table financial_metrics (
  id         uuid primary key default gen_random_uuid(),
  ticker     text not null,
  period     text not null,   -- "2024Q4", "2025Q1"
  per        float,
  pbr        float,
  roe        float,
  eps        float,
  revenue    bigint,
  op_income  bigint,
  net_income bigint,
  updated_at timestamptz default now(),
  unique (ticker, period)
);

-- 기업 개요 (연 1회 갱신)
create table company_profiles (
  ticker      text primary key,
  name        text not null,
  market      text not null,  -- "KOR" | "US"
  sector      text,
  industry    text,
  description text,
  updated_at  timestamptz default now()
);
```

**RAG 이중 활용:**
- Supabase: 구조화 조회 (`get_financials_tool` 온디맨드)
- ChromaDB: 재무 요약 텍스트 청크화 → 시맨틱 검색 컨텍스트로도 활용

---

### 8. 리포트 시스템 설계 (FR-11 상세)

**4종 리포트 타입 및 스케줄:**

| # | 리포트 타입 | report_type | 발행 시각 (KST) | 주요 콘텐츠 |
|---|---|---|---|---|
| 1 | 한국 장 전 브리프 | `KOR_PREMARKET` | 08:00 (UTC 23:00) | KOSPI/KOSDAQ 전일 종가, KOR watchlist 종목, 국내 뉴스 요약 |
| 2 | 한국 장 마감 리포트 | `KOR_CLOSE` | 16:30 (UTC 07:30) | KOSPI/KOSDAQ 당일 종가, KOR watchlist 섹터별 분류, 국내 뉴스 |
| 3 | 미국 장 전 브리프 | `US_PREMARKET` | 22:30 (UTC 13:30) | 유럽 마감, 미국 선물, US watchlist 종목 |
| 4 | 미국 장 마감 리포트 | `US_CLOSE` | 07:00 (UTC 22:00) | S&P500/NASDAQ/DOW 종가, US watchlist 종목, 미국 뉴스 |

**리포트 생성 플로우:**
```
GitHub Actions cron (4개 스케줄) → report_generator.py
  ① 시장 스냅샷 수집 (지수/환율/종목 종가)
  ② Supabase watchlist → 유저별 관심종목 조회 (시장별 분기)
  ③ Agent 기반 뉴스 요약 + 섹터별 종목 인사이트 생성
  ④ market_snapshots 테이블 저장 (공유 데이터)
  ⑤ notifications 테이블 저장 (유저별 개인화 리포트)
```

**Supabase 스키마:**
```sql
-- 리포트/알림 저장
create table public.notifications (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users not null,
  report_type text not null, -- 'KOR_PREMARKET' | 'KOR_CLOSE' | 'US_PREMARKET' | 'US_CLOSE'
  is_read     boolean default false,
  payload     jsonb not null, -- { market, stocks, top_news, market_summary }
  created_at  timestamptz default now()
);

-- 시장 스냅샷 (공유 데이터, 리포트 생성 시 저장)
create table public.market_snapshots (
  id          uuid primary key default gen_random_uuid(),
  report_type text not null,
  snapshot_date date not null,
  payload     jsonb not null,
  created_at  timestamptz default now(),
  unique (report_type, snapshot_date)
);
```

**데이터 파이프라인 보완 필요 사항:**
- KOSPI/KOSDAQ 지수 수집 추가 (`fdr.DataReader("KS11")`, `fdr.DataReader("KQ11")`)
- USD/KRW 환율 수집 추가 (`fdr.DataReader("USD/KRW")`)
- US 파이프라인 cron 분리 (07:00 KST — 미국 장 마감 후)
- daily_prices Supabase 적재 활성화

**프론트엔드 리포트 UI:**
- BottomNav에 리포트 탭 (벨 아이콘) + 미읽음 배지
- `/reports` 리포트 목록 페이지 (날짜별, 4종 아이콘 구분)
- `/reports/[id]` 리포트 상세 페이지 (무드 헤더, 지수, 섹터별 종목, 뉴스)

---

### 9. 구현 로드맵 (마일스톤)

| Phase | 목표 | 주요 산출물 | 상태 |
|---|---|---|---|
| **Phase 1** | 데이터 파이프라인 구축 | 뉴스·공시 수집 → 벡터화 자동화 | ✅ 완료 |
| **Phase 2** | Multi-tool AI 에이전트 | AgentExecutor + 4개 도구, 세그먼트 분기, 스트리밍 | ✅ 완료 |
| **Phase 3** | Next.js + Supabase 프론트엔드 | 인증·watchlist·실시간 가격·인사이트 UI | ✅ 완료 |
| **Phase 4** | EC2 + Vercel 배포 | FastAPI EC2 배포, Next.js Vercel 배포, E2E 검증 | 🔲 진행 예정 |
| **Phase 5** | 재무 데이터 통합 | DART 재무지표, get_financials_tool, Supabase 적재 | ✅ 완료 |
| **Phase 6** | 4종 리포트 시스템 | 한국/미국 장전·장마감 리포트, notifications UI, 데이터 파이프라인 보완 | 🔲 진행 예정 |
| **Phase 7** | 품질 평가 및 최적화 | Recall@5, 도구 선택 정확도, 포트폴리오 문서화 | 🔲 진행 예정 |
