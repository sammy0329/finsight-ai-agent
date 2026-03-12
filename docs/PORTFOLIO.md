# FinSight AI Agent — 포트폴리오 어필 포인트

> 기술적 의사결정 근거, 금융 도메인 특화 설계, 수치 결과를 정리한 문서입니다.

---

## 1. 핵심 기술 스택 선택 근거

### 왜 LangChain AgentExecutor + OpenAI Function Calling인가?

| 대안 | 비교 | 선택 이유 |
|---|---|---|
| Simple RAG (retriever → LLM) | 도구 선택 불가, 단일 정보 소스 | Multi-tool 라우팅 불가 |
| LangGraph | 노드·엣지 설계 필요, 러닝 커브 높음 | MVP 범위 초과 |
| **AgentExecutor + Function Calling** | ✅ | 도구 5개를 동적 라우팅, 검증된 프레임워크 |

**핵심 이유**: 금융 질문의 성격이 다양하다 (뉴스/공시/가격/재무/복합). 단일 RAG로는 "삼성전자 PER이 얼마야?" 같은 구조화된 DB 쿼리 질문을 처리할 수 없다. AgentExecutor는 GPT-4o-mini가 어떤 도구를 쓸지 스스로 판단하게 하여 질문 타입별 적절한 응답을 보장한다.

### 왜 ChromaDB인가?

- **Self-hosted**: Supabase pgvector 대비 embedding 벡터 조작 유연성 높음
- **Python 생태계 통합**: LangChain `Chroma` retriever 기본 지원
- **운영 단순화**: EC2 Docker로 단일 컨테이너 운영, 별도 관리 불필요

### 왜 Supabase인가?

- **Auth 내장**: NextAuth 설정 없이 Row Level Security로 다중 사용자 격리
- **Realtime 준비**: 추후 알림 실시간 push 확장 가능
- **Edge Functions**: 리포트 파이프라인 서버리스 확장 가능

### 왜 Next.js App Router + FastAPI 분리 구조인가?

```
Next.js (Vercel)  ←→  FastAPI (EC2)
     ↓                      ↓
  Supabase              ChromaDB
```

- **FastAPI**: LangChain, FinanceDataReader 등 Python 라이브러리 의존성 격리
- **Next.js**: SSR + React Server Components로 SEO 및 모바일 최적화
- **분리 배포**: FastAPI는 상태 유지(ChromaDB 연결), Next.js는 무상태(Vercel 자동 스케일링)

---

## 2. 금융 도메인 특화 설계

### 세그먼트 기반 응답 분기

3가지 투자 성향(A: 안전추구, B: 위험감수, C: 가치투자)에 따라 동일 질문에도 다른 관점의 답변을 생성한다.

```python
SEGMENT_A → "배당주·채권 중심, 리스크 우선 언급"
SEGMENT_B → "성장주·모멘텀 강조, 상승 기회 부각"
SEGMENT_C → "PER/PBR/ROE 분석, 내재가치 중심"
```

**차별점**: 일반적인 금융 챗봇은 모든 사용자에게 동일한 답변을 제공한다. FinSight는 온보딩에서 수집한 투자 성향을 기반으로 프롬프트를 분기하여 개인화된 인사이트를 제공한다.

### 가격 이상 감지 (Z-score 기반)

```python
# 최근 20일 수익률의 Z-score 계산
z = (최근수익률 - 평균수익률) / 표준편차
# |Z| > 2 → 급등/급락 이상 감지 → 배지 표시 + 인사이트 우선 제공
```

단순 등락률 표시 대신 통계적 이상치 탐지로 노이즈를 줄이고 실제 이벤트성 움직임을 포착한다.

### 4종 리포트 시스템

한국·미국 시장의 장전·마감 시점에 각각 브리프와 리포트를 생성한다.

| 리포트 타입 | 시각 (KST) | 내용 |
|---|---|---|
| KOR_PREMARKET | 08:00 | 전일 미국 마감 요약, 금일 한국 장 전망 |
| KOR_CLOSE | 16:30 | 한국 장 마감 요약, 관심종목 등락, 주요 공시 |
| US_PREMARKET | 22:30 | 아시아 마감 요약, 금일 미국 장 전망 |
| US_CLOSE | 07:00 | 미국 장 마감 요약, S&P500/NASDAQ/DOW |

### 면책 고지 설계

AgentExecutor 시스템 프롬프트에 투자 권유 금지 문구를 포함하여 모든 응답이 투자 의견이 아닌 정보 제공임을 명시한다.

---

## 3. 파이프라인 설계 의사결정

### 이중 cron 구조 (KOR + US 분리)

```
KOR 파이프라인 (UTC 07:30): 한국 장 마감 → ChromaDB/Supabase 적재
US 파이프라인  (UTC 22:00): 미국 장 마감 → ChromaDB/Supabase 적재
리포트 파이프라인 (UTC 07:45 / 22:45 / 23:00 / 13:30): 리포트 생성 → 알림 삽입
```

**의사결정 근거**: 초기 단일 cron(KST 16:30)은 미국 주가를 전전일 데이터로 수집하는 타이밍 불일치 문제가 있었다. 시장별 분리 실행으로 데이터 신선도를 보장한다.

### TDD 기반 개발 (389개 테스트)

전체 백엔드 모듈을 TDD(RED→GREEN→REFACTOR) 사이클로 개발하여:
- 외부 의존성(yfinance, ChromaDB, Supabase, OpenAI) 모두 Mock 처리
- 신규 기능 추가 시 기존 동작 보장 (regression 방지)
- 커버리지 95%+

---

## 4. 수치 결과 (Phase 4 배포 후 측정 예정)

| 지표 | 목표값 | 실측값 |
|---|---|---|
| Recall@5 | ≥ 80% | — |
| 도구 선택 정확도 | ≥ 85% | — |
| 환각 비율 | ≤ 10% | — |
| P95 인사이트 응답 시간 | < 5초 | — |
| 테스트 커버리지 | ≥ 95% | 95%+ |
| 총 테스트 케이스 | — | 389개 |

> 측정 스크립트: `ai-server/scripts/eval_recall.py`, `ai-server/scripts/eval_tool_selection.py`

---

## 5. 트레이드오프 및 한계

| 항목 | 선택 | 포기한 것 |
|---|---|---|
| gpt-4o-mini | 저비용, 빠른 응답 | gpt-4o 대비 복잡한 추론 품질 |
| ChromaDB (self-hosted) | 운영 제어권 | 관리형 벡터 DB의 HA/백업 |
| 일별 뉴스 수집 (배치) | 구현 단순성 | 실시간 뉴스 반영 |
| Supabase 무료 티어 | 초기 비용 절감 | 트래픽 급증 시 제한 |

---

## 6. 확장 가능성

- **실시간 스트리밍**: SSE 기반 인사이트 스트리밍 이미 구현 완료
- **다중 시장 확장**: `market` 필드 기반 설계로 일본·유럽 시장 추가 가능
- **A/B 테스트**: 세그먼트별 프롬프트 실험 인프라 내장
- **MCP 확장**: Claude Desktop MCP Server로 확장 가능한 Tool 구조
