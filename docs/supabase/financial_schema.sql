-- ============================================================
-- FinSight Agent — Financial Data Schema (Epic 5-1)
-- Supabase Dashboard > SQL Editor 에서 실행
-- ============================================================

-- ────────────────────────────────
-- 1. financial_metrics
--    분기별 재무지표 (PER, PBR, ROE, 매출, 영업이익 등)
-- ────────────────────────────────
create table public.financial_metrics (
  id          bigserial primary key,
  ticker      text not null,
  period      text not null,           -- "2025Q1" 형식
  per         numeric(10, 4),          -- Price-to-Earnings Ratio
  pbr         numeric(10, 4),          -- Price-to-Book Ratio
  roe         numeric(10, 6),          -- Return on Equity (소수점)
  eps         numeric(14, 2),          -- Earnings per Share
  revenue     bigint,                  -- 매출액
  op_income   bigint,                  -- 영업이익
  net_income  bigint,                  -- 순이익
  created_at  timestamptz default now(),
  updated_at  timestamptz default now(),
  unique (ticker, period)
);

create index idx_financial_metrics_ticker on public.financial_metrics(ticker, period desc);

alter table public.financial_metrics enable row level security;

create policy "재무지표 전체 조회 허용"
  on public.financial_metrics for select
  using (true);

-- Service Role만 insert/update 가능 (파이프라인 전용)
create policy "서비스 롤 재무지표 쓰기"
  on public.financial_metrics for insert
  with check (auth.role() = 'service_role');

create policy "서비스 롤 재무지표 수정"
  on public.financial_metrics for update
  using (auth.role() = 'service_role');


-- ────────────────────────────────
-- 2. company_profiles
--    기업 개요 (업종, 사업내용 등)
-- ────────────────────────────────
create table public.company_profiles (
  ticker      text primary key,
  name        text not null,
  market      text not null,           -- "KOR" 또는 "US"
  sector      text,
  industry    text,
  description text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

alter table public.company_profiles enable row level security;

create policy "기업 개요 전체 조회 허용"
  on public.company_profiles for select
  using (true);

create policy "서비스 롤 기업 개요 쓰기"
  on public.company_profiles for insert
  with check (auth.role() = 'service_role');

create policy "서비스 롤 기업 개요 수정"
  on public.company_profiles for update
  using (auth.role() = 'service_role');


-- ────────────────────────────────
-- 3. updated_at 자동 갱신 트리거
-- ────────────────────────────────
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trigger_financial_metrics_updated_at
  before update on public.financial_metrics
  for each row execute function public.update_updated_at_column();

create trigger trigger_company_profiles_updated_at
  before update on public.company_profiles
  for each row execute function public.update_updated_at_column();
