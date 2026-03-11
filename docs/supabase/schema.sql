-- ============================================================
-- FinSight Agent — Supabase Schema
-- Supabase Dashboard > SQL Editor 에서 실행
-- ============================================================

-- ────────────────────────────────
-- 1. profiles
--    사용자 투자 성향 (A/B/C)
-- ────────────────────────────────
create table public.profiles (
  user_id   uuid primary key references auth.users(id) on delete cascade,
  segment   char(1) not null check (segment in ('A', 'B', 'C')),
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "본인 프로필만 조회"
  on public.profiles for select
  using (auth.uid() = user_id);

create policy "본인 프로필만 수정"
  on public.profiles for all
  using (auth.uid() = user_id);


-- ────────────────────────────────
-- 2. stocks
--    KRX + S&P500 종목 목록 (파이프라인이 적재)
-- ────────────────────────────────
create table public.stocks (
  ticker  text primary key,
  name    text not null,
  market  text not null check (market in ('KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE', 'S&P500'))
);

-- 종목 검색은 모든 사용자가 가능 (로그인 불필요)
alter table public.stocks enable row level security;

create policy "종목 목록 전체 조회 허용"
  on public.stocks for select
  using (true);


-- ────────────────────────────────
-- 3. daily_prices
--    전일 종가 + 등락률 (파이프라인이 매일 적재)
-- ────────────────────────────────
create table public.daily_prices (
  id         bigserial primary key,
  ticker     text not null references public.stocks(ticker) on delete cascade,
  date       date not null,
  close      numeric(12, 2) not null,
  change_pct numeric(6, 2) not null,
  unique (ticker, date)
);

create index idx_daily_prices_ticker_date on public.daily_prices(ticker, date desc);

alter table public.daily_prices enable row level security;

create policy "가격 데이터 전체 조회 허용"
  on public.daily_prices for select
  using (true);


-- ────────────────────────────────
-- 4. watchlist
--    사용자 관심 종목
-- ────────────────────────────────
create table public.watchlist (
  id        bigserial primary key,
  user_id   uuid not null references auth.users(id) on delete cascade,
  ticker    text not null references public.stocks(ticker) on delete cascade,
  name      text not null,
  market    text not null,
  added_at  timestamptz default now(),
  unique (user_id, ticker)
);

create index idx_watchlist_user_id on public.watchlist(user_id);

alter table public.watchlist enable row level security;

create policy "본인 watchlist만 접근"
  on public.watchlist for all
  using (auth.uid() = user_id);


-- ────────────────────────────────
-- 5. insight_history
--    인사이트 질문/답변 이력
-- ────────────────────────────────
create table public.insight_history (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  ticker      text not null,
  stock_name  text not null,
  query       text not null,
  answer      text not null,
  sources     text[] default '{}',
  created_at  timestamptz default now()
);

create index idx_insight_history_user_id on public.insight_history(user_id, created_at desc);

alter table public.insight_history enable row level security;

create policy "본인 이력만 접근"
  on public.insight_history for all
  using (auth.uid() = user_id);


-- ────────────────────────────────
-- 6. 회원가입 시 profiles 자동 생성 트리거
--    (onboarding 전 segment='A' 기본값으로 생성)
-- ────────────────────────────────
create or replace function public.handle_new_user()
returns trigger as $$
begin
  -- onboarding에서 upsert 하므로 기본값만 삽입
  insert into public.profiles (user_id, segment)
  values (new.id, 'A')
  on conflict (user_id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
