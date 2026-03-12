# FinSight Agent — Frontend

FinSight Agent의 Next.js 14 프론트엔드입니다.
사용자 인증, 관심종목 관리, 실시간 가격, AI 인사이트 스트리밍, 모닝 브리프 알림 UI를 제공합니다.

---

## 기술 스택

| 항목 | 기술 |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| 인증 / DB | Supabase Auth + Supabase PostgreSQL |
| 실시간 가격 | Yahoo Finance API (lib/yahoo.ts) |
| 배포 | Vercel |

---

## 디렉토리 구조

```
frontend/
├── app/
│   ├── (auth)/             # 인증 관련 페이지
│   │   ├── login/          # 로그인 / 회원가입
│   │   └── onboarding/     # 투자 성향 세그먼트 선택
│   ├── (main)/             # 메인 앱 (인증 필요)
│   │   ├── page.tsx        # 홈 — watchlist 카드, 시장 요약
│   │   ├── search/         # 종목 검색 및 watchlist 관리
│   │   ├── insight/[ticker]/ # 종목별 AI 인사이트
│   │   ├── history/        # 인사이트 이력
│   │   ├── notifications/  # 모닝 브리프 알림 목록
│   │   └── settings/       # 설정 (세그먼트 변경, 로그아웃)
│   └── api/
│       ├── insight/        # FastAPI SSE 스트리밍 프록시
│       └── stocks/
│           ├── search/     # 종목 검색 API
│           └── anomaly/[ticker]/ # 가격 이상 감지 API
├── components/
│   └── AnomalyBadge.tsx    # 급등/급락 배지 (클라이언트 컴포넌트)
├── lib/
│   ├── supabase/
│   │   ├── client.ts       # 브라우저용 Supabase 클라이언트
│   │   └── server.ts       # 서버 컴포넌트용 Supabase 클라이언트
│   └── yahoo.ts            # Yahoo Finance 가격·시장 요약 조회
├── types/
│   └── index.ts            # Segment, PriceData 등 공통 타입
└── middleware.ts            # 인증 라우트 보호
```

---

## 로컬 개발 실행

### 1. 환경변수 설정

```bash
cp .env.local.example .env.local
```

`.env.local` 파일에 아래 값을 입력합니다.

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
FASTAPI_URL=http://localhost:8000
INTERNAL_API_KEY=your_shared_key_with_fastapi
```

### 2. 의존성 설치 및 실행

```bash
npm install
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000) 접속.

> FastAPI + ChromaDB가 실행 중이어야 인사이트 기능이 동작합니다.
> 루트 디렉토리에서 `docker compose up -d chromadb fastapi` 실행 후 개발 서버를 시작하세요.

---

## 주요 명령어

```bash
npm run dev        # 개발 서버 실행 (http://localhost:3000)
npm run build      # 프로덕션 빌드
npm run lint       # ESLint 검사
npx tsc --noEmit  # TypeScript 타입 검사
```

---

## 핵심 컴포넌트

### lib/yahoo.ts

Yahoo Finance API로 실시간 가격·시장 요약을 조회합니다.

```typescript
fetchPrice(ticker, market)       // 종목 단건 조회
fetchPrices(tickers, market)     // 종목 다건 조회 (관심종목 홈)
fetchMarketSummary()             // KOSPI, NASDAQ, 원/달러 (revalidate: 30분)
```

### AnomalyBadge.tsx

페이지 초기 렌더를 차단하지 않는 클라이언트 컴포넌트.
`/api/stocks/anomaly/[ticker]` 를 비동기로 호출하여 급등/급락 배지를 표시합니다.

### InsightClient.tsx

SSE 스트리밍을 수신하여 AI 인사이트를 실시간으로 렌더링합니다.

```
POST /api/insight → FastAPI /api/ai/insight/stream
→ ReadableStream → data: {token}\n\n 파싱 → setInsight(fullText)
```

---

## API Routes

| 경로 | 메서드 | 설명 |
|---|---|---|
| `/api/insight` | POST | FastAPI SSE 스트리밍 프록시 |
| `/api/stocks/search` | GET | Supabase 종목 검색 (ILIKE) |
| `/api/stocks/anomaly/[ticker]` | GET | FastAPI 가격 이상 감지 프록시 |

---

## 배포 (Vercel)

main 브랜치에 push하면 Vercel이 자동으로 빌드 및 배포합니다.

Vercel 대시보드에서 아래 환경변수를 등록해야 합니다.

| 변수명 | 설명 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `FASTAPI_URL` | EC2 탄력적 IP (`http://{IP}:8000`) |
| `INTERNAL_API_KEY` | FastAPI 내부 인증키 |
