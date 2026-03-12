# FinSight Agent

> 고객 세그먼트 기반 맞춤형 투자 인사이트 AI 에이전트

뉴스·공시·실시간 가격·재무 데이터를 **Multi-tool LangChain Agent**로 연계하여, 사용자의 투자 성향(안전추구형·위험감수형·가치투자형)에 따라 검색 전략과 답변 관점을 동시에 분기하는 개인화 투자 인사이트 웹 서비스.

---

## GPT 래퍼와의 차별점

일반적인 RAG 챗봇은 `질문 → 벡터 검색 → GPT 답변` 단계로 끝납니다.
FinSight Agent는 세 가지 측면에서 이를 넘어섭니다.

### 1. Multi-tool Agent — Agent가 데이터 소스를 스스로 선택

```
유저: "삼성전자 오늘 왜 이렇게 떨어졌어?"

Agent 판단:
  1. price_anomaly_tool  → Z-score 3.1 (통계적 이상 감지)
  2. search_news_tool    → 관련 뉴스 Top-5 (ChromaDB RAG)
  3. get_dart_tool       → 최근 30일 공시 확인

→ 세 결과를 세그먼트 B형(위험감수) 관점으로 종합
```

단순 검색이 아니라 **Agent가 질문 유형에 따라 필요한 도구를 판단·조합**합니다.

| 도구 | 데이터 소스 | 역할 |
|---|---|---|
| `search_news_tool` | ChromaDB (뉴스·공시 벡터 DB) | 관련 뉴스 시맨틱 검색 |
| `get_dart_tool` | 금융감독원 DART API | 기업 공시 직접 조회 |
| `get_price_tool` | Yahoo Finance API | 실시간 종가·등락률 |
| `price_anomaly_tool` | FinanceDataReader + 통계 | Z-score 기반 이상 감지 |
| `get_financials_tool` | Supabase (DART 재무제표) | PER, PBR, ROE, 매출, 영업이익 |

### 2. 세그먼트 기반 이중 분기 — 검색 전략 + 프롬프트 동시 분기

동일한 질문이라도 사용자 투자 성향에 따라 **검색 메타데이터 필터와 시스템 프롬프트가 모두 달라집니다**.

| 세그먼트 | 검색 전략 | 답변 관점 |
|---|---|---|
| A형 (안전추구) | 리스크·배당 카테고리 우선 필터 | 보수적, 리스크 강조 |
| B형 (위험감수) | 가격 이상·모멘텀 섹터 우선 필터 | 공격적, 기회 강조 |
| C형 (가치투자) | 공시·실적·재무 문서 우선 필터 | 분석적, 펀더멘털 중심 |

### 3. 가격 이상 감지 — 데이터 기반 트리거

최근 20일 표준편차 기반 Z-score를 산출하여 **통계적으로 비정상적인 가격 변동을 자동 감지**하고, 그 원인을 뉴스·공시 데이터로 설명합니다.

### 4. 4종 리포트 시스템 — 한국/미국 장전·장마감 자동 인사이트

한국/미국 장전·장마감 4종 리포트를 자동 생성하여 인앱 알림으로 전달합니다. 사용자가 앱을 열기 전에 오늘의 투자 정보가 준비되어 있습니다.

| 리포트 | 시각 (KST) | 주요 콘텐츠 |
|---|---|---|
| 한국 장 전 브리프 | 08:00 | KOSPI/KOSDAQ 전일 종가, KOR watchlist, 국내 뉴스 |
| 한국 장 마감 리포트 | 16:30 | KOSPI/KOSDAQ 당일, KOR watchlist 섹터별, 국내 뉴스 |
| 미국 장 전 브리프 | 22:30 | 유럽 마감, 미국 선물, US watchlist |
| 미국 장 마감 리포트 | 07:00 | S&P500/NASDAQ/DOW, US watchlist, 미국 뉴스 |

---

## 아키텍처

```mermaid
flowchart TD
    Client["Client (Browser)"]

    subgraph Vercel["Frontend & BFF — Next.js (Vercel)"]
        NX["Next.js 14 App Router\n인증 · watchlist · 가격 UI · 알림"]
        APIRoute["/api/insight — SSE 프록시"]
    end

    subgraph Supabase["Supabase Cloud"]
        SA["Auth"]
        SDB["PostgreSQL\nprofiles · watchlist · insight_history\nfinancial_metrics · notifications\nmarket_snapshots"]
    end

    subgraph EC2["AWS EC2 t3.micro — Docker Compose"]
        FA["FastAPI :8000\nLangChain AgentExecutor"]
        subgraph Tools["Agent Tools (5개)"]
            T1["search_news_tool"]
            T2["get_dart_tool"]
            T3["get_price_tool"]
            T4["price_anomaly_tool"]
            T5["get_financials_tool"]
        end
        Chroma["ChromaDB :8001"]
    end

    subgraph ReportPipeline["Report Pipeline — GitHub Actions"]
        R1["KOR 장전 브리프\n08:00 KST"]
        R2["KOR 장마감 리포트\n16:30 KST"]
        R3["US 장전 브리프\n22:30 KST"]
        R4["US 장마감 리포트\n07:00 KST"]
    end

    subgraph Pipeline["GitHub Actions"]
        P1["뉴스 파이프라인\n평일 16:30 KST"]
        P2["재무 파이프라인\n분기 1회"]
    end

    Client --> NX
    NX --> SA & SDB & APIRoute
    APIRoute --> FA
    FA --> T1 & T2 & T3 & T4 & T5
    T1 --> Chroma
    T5 --> SDB
    R1 & R2 & R3 & R4 --> SDB & FA
    P1 --> Chroma
    P2 --> SDB
```

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| Frontend & BFF | TypeScript · Next.js 14 (App Router) · Tailwind CSS · Vercel |
| 인증 / DB | Supabase Auth · Supabase PostgreSQL · RLS |
| AI Backend | Python 3.11 · FastAPI · LangChain AgentExecutor · ChromaDB |
| LLM / Embedding | OpenAI GPT-4o-mini · text-embedding-3-small |
| 실시간 가격 | Yahoo Finance API |
| Pipeline (뉴스) | GitHub Actions · Naver Search API · NewsAPI · OpenDart API |
| Pipeline (재무) | GitHub Actions · DART 재무제표 API · Supabase |
| 리포트 시스템 (4종) | GitHub Actions cron · report_generator.py |
| Infra | AWS EC2 t3.micro · Docker Compose |

---

## 프로젝트 구조

```
finsight-ai-agent/
├── frontend/               # Next.js 14 프론트엔드 + API Route
│   ├── app/
│   │   ├── (auth)/         # 로그인·온보딩
│   │   ├── (main)/         # 홈·검색·인사이트·이력·설정·알림
│   │   └── api/            # /api/insight (SSE 프록시)
│   ├── components/         # AnomalyBadge 등 재사용 컴포넌트
│   └── lib/
│       ├── supabase/       # 브라우저·서버 클라이언트
│       └── yahoo.ts        # 실시간 가격·시장 요약
├── ai-server/              # FastAPI AI 에이전트 서버
│   └── app/
│       ├── api/            # FastAPI 라우터
│       ├── agent/          # LangChain AgentExecutor + 5개 Tools
│       ├── pipeline/       # 데이터 수집·정제·벡터화
│       └── core/           # 설정·공통 유틸
├── ai-server/app/pipeline/ # 리포트 생성 파이프라인 (report_generator.py)
├── docker/                 # Dockerfile 모음
├── docs/                   # PRD · TECH_STACK · TASK · DEPLOYMENT
└── docker-compose.yml
```

---

## 로컬 실행

### 사전 준비

- Node.js 20+, Docker / Docker Compose
- Python 3.11+, Poetry

```bash
# Poetry 설치 (최초 1회)
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### 실행

```bash
git clone https://github.com/sammy0329/finsight-ai-agent.git
cd finsight-ai-agent

# 환경변수 설정
cp .env.example .env                              # FastAPI용 .env 작성
cp frontend/.env.local.example frontend/.env.local  # Next.js 환경변수 작성

# Python 의존성 설치
cd ai-server && poetry install && cd ..

# ChromaDB + FastAPI 실행
docker compose up -d chromadb fastapi

# Next.js 개발 서버
cd frontend && npm install && npm run dev
```

### 파이프라인 수동 실행

```bash
cd ai-server
export $(cat ../.env | grep -v '^#' | xargs)
CHROMA_HOST=localhost CHROMA_PORT=8001 \
  poetry run python -m app.pipeline.run_pipeline
```

### 서비스 URL

| 서비스 | URL |
|---|---|
| Next.js | http://localhost:3000 |
| FastAPI Swagger | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |

---

## 환경변수

| 변수명 | 위치 | 설명 |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | frontend/.env.local | Supabase 프로젝트 URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend/.env.local | Supabase anon key |
| `FASTAPI_URL` | frontend/.env.local | FastAPI 서버 주소 |
| `INTERNAL_API_KEY` | frontend/.env.local + .env | Next.js ↔ FastAPI 내부 인증키 (동일 값) |
| `OPENAI_API_KEY` | .env | OpenAI API 키 |
| `DART_API_KEY` | .env | 금융감독원 DART API 키 |
| `NAVER_CLIENT_ID/SECRET` | .env | Naver Search API 키 |
| `NEWS_API_KEY` | .env | NewsAPI 키 |

---

## 구현 로드맵

| Phase | 목표 | 상태 |
|---|---|---|
| Phase 1 | 데이터 파이프라인 (뉴스·공시 수집 → ChromaDB) | ✅ 완료 |
| Phase 2 | Multi-tool AI 에이전트 (AgentExecutor + 4개 도구) | ✅ 완료 |
| Phase 3 | Next.js + Supabase 프론트엔드 | ✅ 완료 |
| Phase 4 | EC2 + Vercel 배포 | 🔲 진행 예정 |
| Phase 5 | 재무 데이터 통합 (DART PER/PBR/ROE + get_financials_tool) | ✅ 완료 |
| Phase 6 | 4종 리포트 시스템 (한국/미국 장전·장마감 리포트 + notifications UI) | 🔲 진행 예정 |
| Phase 7 | 품질 평가 및 포트폴리오 문서화 | 🔲 진행 예정 |

---

## 문서

| 문서 | 설명 |
|---|---|
| [PRD.md](./docs/PRD.md) | 제품 요구사항 정의서 — 기능·비기능 요구사항, Agent 도구 설계 |
| [TECH_STACK.md](./docs/TECH_STACK.md) | 기술 스택 명세 — 아키텍처 다이어그램, 시퀀스, 기술 선택 근거 |
| [TASK.md](./docs/TASK.md) | Phase/Epic/Task 단위 작업 명세 및 진행 상태 |
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | 배포 전략 및 인프라 구성 (EC2, Vercel, Lambda) |

---

> ⚠️ 본 서비스는 정보 제공 목적이며 투자를 권유하지 않습니다. 모든 투자 판단과 책임은 사용자 본인에게 있습니다.
