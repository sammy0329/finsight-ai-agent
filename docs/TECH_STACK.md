# 기술 스택 명세서 (Tech Stack)

**프로젝트명:** FinSight Agent
**연관 문서:** [PRD.md](./PRD.md)

---

## 전체 시스템 아키텍처

```mermaid
flowchart TD
    Client["Client (Browser)"]

    subgraph SpringBoot["Main Backend — Spring Boot (Java 17)"]
        direction LR
        Auth["사용자 인증 / JWT"]
        UserDB["회원 · 세그먼트 DB 관리"]
        ClientAPI["클라이언트 REST API"]
        InternalCall["AI 서버 통신 (WebClient)"]
    end

    subgraph FastAPI["AI & Data Backend — FastAPI (Python 3.11)"]
        direction LR
        RAG["RAG 에이전트 (LangChain)"]
        Prompt["세그먼트별 프롬프트 분기"]
        VectorMgr["Vector DB 관리"]
    end

    subgraph Storage["Storage"]
        direction LR
        MySQL["MySQL 8\n(users, profiles, history)"]
        ChromaDB["ChromaDB\n(financial_news_kor/us)"]
    end

    subgraph ExternalAPIs["External APIs"]
        direction LR
        LLM["OpenAI GPT-4o-mini"]
        Embedding["OpenAI Embeddings\ntext-embedding-3-small"]
    end

    subgraph Pipeline["Data Pipeline — GitHub Actions (매일 16:30 KST)"]
        direction LR
        Collect["① Collect\nFDR / DART / Naver / NewsAPI"]
        Preprocess["② Preprocess\n정제 · 메타데이터 부착"]
        Chunk["③ Chunk\nRecursiveTextSplitter\n500토큰 / 50 오버랩"]
        Embed["④ Embed\nOpenAI Embeddings 호출"]
        Load["⑤ Load\nChromaDB upsert"]
        Notify["⑥ Notify\n실패 시 Slack 알림"]
    end

    Client -->|"REST (JWT)"| ClientAPI
    ClientAPI --> Auth
    ClientAPI --> UserDB
    UserDB --> MySQL
    ClientAPI --> InternalCall
    InternalCall -->|"POST /api/ai/insight\n(X-Internal-Key)"| RAG
    RAG --> Prompt
    Prompt --> VectorMgr
    VectorMgr -->|"유사도 검색"| ChromaDB
    RAG -->|"LLM 호출"| LLM
    Embed -->|"임베딩 생성"| Embedding

    Collect --> Preprocess --> Chunk --> Embed --> Load --> ChromaDB
    Load -->|"실패"| Notify
```

---

## 인사이트 요청 시퀀스

```mermaid
sequenceDiagram
    actor Client
    participant SB as Spring Boot
    participant MySQL
    participant FA as FastAPI
    participant Chroma as ChromaDB
    participant LLM as OpenAI GPT-4o-mini

    Client->>SB: GET /api/insight (JWT 포함)
    SB->>MySQL: 사용자 세그먼트 조회
    MySQL-->>SB: segment = "A" (안전추구형)

    SB->>FA: POST /api/ai/insight\n{"user_segment":"A","query":"시장 이슈 요약"}
    FA->>Chroma: 유사도 검색 (market=KOR, date=today)
    Chroma-->>FA: Top-5 관련 청크 반환
    FA->>LLM: 세그먼트 A 시스템 프롬프트 + 청크 컨텍스트
    LLM-->>FA: 마크다운 인사이트 텍스트

    FA-->>SB: {"insight": "..."}
    SB-->>Client: 최종 인사이트 응답
```

---

## 데이터 파이프라인 흐름

```mermaid
flowchart LR
    subgraph Sources["데이터 소스"]
        FDR["FinanceDataReader\n국내 주가/재무"]
        DART["OpenDart API\n기업 공시"]
        Naver["Naver Search API\n국내 뉴스"]
        NewsAPI["NewsAPI\n미국 뉴스"]
    end

    subgraph Process["전처리"]
        Clean["정제\n중복 제거 · 노이즈 제거"]
        Meta["메타데이터 부착\nsource · ticker · sentiment"]
        Split["청킹\n500토큰 / 50 오버랩"]
    end

    subgraph Vectorize["벡터화"]
        EmbedAPI["OpenAI\ntext-embedding-3-small"]
        Upsert["ChromaDB upsert\nfinancial_news_kor/us"]
    end

    FDR & DART & Naver & NewsAPI --> Clean
    Clean --> Meta --> Split --> EmbedAPI --> Upsert
```

---

## 1. Main Backend — Spring Boot

| 항목 | 기술 | 버전 | 선택 근거 |
|---|---|---|---|
| Language | Java | 17 LTS | Record, Sealed class 등 현대적 문법 지원 |
| Framework | Spring Boot | 3.x | 자동 설정, 풍부한 생태계, 금융권 실무 표준 |
| ORM | Spring Data JPA + Hibernate | Boot 내장 | 객체-관계 매핑 자동화, JPQL 활용 |
| Database | MySQL | 8.x | 금융 트랜잭션 데이터에 적합한 RDBMS |
| 인증 | Spring Security + JWT | - | Stateless 인증, MSA 환경 토큰 기반 관리 |
| API 문서화 | SpringDoc OpenAPI (Swagger) | 2.x | REST API 명세 자동 생성 |
| HTTP Client | WebClient (Spring WebFlux) | Boot 내장 | FastAPI와의 비동기 내부 통신 |
| 빌드 도구 | Gradle | 8.x | 빠른 빌드, Kotlin DSL 지원 |

```groovy
// build.gradle
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-security'
    implementation 'org.springframework.boot:spring-boot-starter-webflux'
    implementation 'io.jsonwebtoken:jjwt-api:0.12.x'
    implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.x'
    runtimeOnly 'com.mysql:mysql-connector-j'
}
```

---

## 2. AI & Data Backend — FastAPI

| 항목 | 기술 | 버전 | 선택 근거 |
|---|---|---|---|
| Language | Python | 3.11+ | 최신 LTS, 성능 개선 및 타입 힌트 강화 |
| Framework | FastAPI | 0.110+ | 비동기 네이티브, 자동 OpenAPI 문서, Pydantic 통합 |
| AI Orchestration | LangChain | 0.2+ | RAG 체인, 프롬프트 템플릿, 에이전트 구성 표준 |
| LLM | OpenAI GPT-4o-mini | - | 비용 효율적, 빠른 응답, 금융 텍스트 생성 충분 |
| Embedding | OpenAI text-embedding-3-small | - | ada-002 대비 약 5배 저렴, 성능 동등, 1536차원 |
| Vector DB | ChromaDB | 0.5+ | 로컬/서버 모드, 메타데이터 필터링 지원, 무료 |
| 데이터 검증 | Pydantic | v2 | 요청/응답 스키마 자동 검증 |
| HTTP 서버 | Uvicorn | - | ASGI 고성능 서버 |
| 패키지 관리 | Poetry | - | 의존성 락파일 관리, 가상환경 격리 |

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110"
uvicorn = {extras = ["standard"], version = "^0.29"}
langchain = "^0.2"
langchain-openai = "^0.1"
langchain-chroma = "^0.1"
chromadb = "^0.5"
pydantic = "^2.0"
python-jose = {extras = ["cryptography"], version = "^3.3"}
httpx = "^0.27"
```

---

## 3. Data Pipeline — 수집 및 전처리

| 항목 | 기술 | 선택 근거 |
|---|---|---|
| 스케줄러 | GitHub Actions (cron) | 별도 서버 불필요, CI/CD와 통합 관리 |
| 국내 주가/재무 | FinanceDataReader 0.9+ | KRX, KOSPI/KOSDAQ 데이터 무료 수집 |
| 국내 공시 | 금융감독원 OpenDart API | 사업보고서, 분기보고서 구조화 수집 |
| 국내 뉴스 | Naver Search API | 실시간 금융 뉴스 수집 |
| 미국 뉴스 | NewsAPI | 영문 금융 뉴스 수집 |
| 데이터 처리 | pandas 2.x | 주가 데이터 정제 및 변환 |
| HTTP 요청 | httpx | 비동기 API 호출 |
| 텍스트 분할 | LangChain RecursiveCharacterTextSplitter | 500토큰 / 50 오버랩, 문장 단위 경계 |

```yaml
# .github/workflows/daily-pipeline.yml
name: Daily Financial Data Pipeline
on:
  schedule:
    - cron: '30 7 * * 1-5'  # 평일 16:30 KST (UTC+9)

jobs:
  pipeline:
    steps:
      - name: Collect     # DART, Naver API, NewsAPI, FDR 수집
      - name: Preprocess  # 정제, 메타데이터 부착, JSON 구조화
      - name: Embed       # OpenAI Embedding API 호출
      - name: Load        # ChromaDB upsert
      - name: Notify      # 실패 시 Slack 알림 (최대 2회 재시도)
```

---

## 4. 데이터베이스

### MySQL — 관계형 DB (Spring Boot)

| 테이블 | 주요 컬럼 | 용도 |
|---|---|---|
| `users` | id, email, password_hash, created_at | 사용자 기본 정보 |
| `user_profiles` | user_id, segment(A/B/C), risk_score | 투자 성향 세그먼트 |
| `insight_history` | user_id, query, response, created_at | AI 인사이트 요청/응답 이력 |

### ChromaDB — Vector DB (FastAPI)

| 컬렉션명 | 설명 |
|---|---|
| `financial_news_kor` | 국내 뉴스 및 공시 청크 |
| `financial_news_us` | 미국 뉴스 청크 |

```json
// 청크 메타데이터 스키마
{
  "source": "naver_news | dart | newsapi",
  "published_at": "2025-03-10T14:30:00",
  "collected_at": "2025-03-10T16:35:00",
  "market": "KOR | US",
  "related_tickers": ["005930", "000660"],
  "category": "semiconductor | finance | energy",
  "sentiment": "positive | negative | neutral"
}
```

---

## 5. 인증 및 보안

```mermaid
flowchart LR
    Client -->|"① 로그인 요청"| SB["Spring Boot"]
    SB -->|"② BCrypt 검증"| MySQL
    MySQL -->|"③ 사용자 확인"| SB
    SB -->|"④ Access Token 30분\nRefresh Token 7일"| Client
    Client -->|"⑤ Bearer Token"| SB
    SB -->|"⑥ X-Internal-Key\n내부 서비스 인증"| FA["FastAPI"]
```

| 항목 | 방식 | 비고 |
|---|---|---|
| 사용자 인증 | JWT (Access + Refresh Token) | Access: 30분, Refresh: 7일 |
| 내부 서비스 통신 | Internal API Key (`X-Internal-Key` 헤더) | Spring Boot ↔ FastAPI 인증 |
| 민감 정보 관리 | GitHub Actions Secrets / 환경변수 | OpenAI API Key, DB 패스워드 등 |
| 패스워드 저장 | BCrypt (strength 12) | Spring Security 기본 제공 |

---

## 6. 개발 환경 및 인프라

| 항목 | 기술 | 비고 |
|---|---|---|
| 컨테이너화 | Docker + Docker Compose | 로컬 개발 환경 통합 실행 |
| 버전 관리 | Git + GitHub | PR 기반 코드 리뷰 |
| CI/CD | GitHub Actions | 빌드/테스트 자동화 + 데이터 파이프라인 |
| API 테스트 | Postman / Swagger UI | 수동 검증 |
| 코드 품질 (Python) | Ruff (Linter), Black (Formatter) | pre-commit hook 적용 |
| 코드 품질 (Java) | Checkstyle | Google Java Style 준수 |

```yaml
# docker-compose.yml 서비스 구성
services:
  mysql:        # port 3306
  spring-boot:  # port 8080  depends_on: mysql
  fastapi:      # port 8000  depends_on: chromadb
  chromadb:     # port 8001
```

---

## 7. 기술 선택 요약 및 근거

| 레이어 | 선택 기술 | 대안 | 선택 근거 |
|---|---|---|---|
| Main Backend | Spring Boot | Django, NestJS | Java 생태계의 금융권 표준, 강력한 Spring Security |
| AI Backend | FastAPI | Flask, Django | 비동기 네이티브, Pydantic 자동 검증, LangChain과 궁합 |
| Vector DB | ChromaDB | Pinecone, Weaviate | 로컬 실행 가능, 무료, 메타데이터 필터 지원 |
| Embedding | text-embedding-3-small | text-embedding-ada-002 | 비용 5배 절감, 성능 동등 |
| LLM | GPT-4o-mini | GPT-4o, Claude 3.5 Sonnet | 비용 효율적, RAG 기반이므로 컨텍스트 보완 가능 |
| Pipeline | GitHub Actions | Airflow, Prefect | 별도 인프라 불필요, 프로젝트 규모에 적합 |
| RDBMS | MySQL | PostgreSQL | 범용성, 관리 용이성, 금융 트랜잭션 처리 |
