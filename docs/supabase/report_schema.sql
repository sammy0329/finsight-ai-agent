-- ============================================================
-- FinSight Agent — 리포트 시스템 스키마 (Epic 6-1)
-- Supabase Dashboard > SQL Editor 에서 실행
-- ============================================================

-- ────────────────────────────────
-- notifications
--   사용자별 리포트 알림 (4종)
--   report_type: 'KOR_PREMARKET' | 'KOR_CLOSE' | 'US_PREMARKET' | 'US_CLOSE'
--   payload JSONB 구조:
--   {
--     "market_summary": "...",
--     "market": {
--       "kospi": {"value": 2612, "change_pct": 0.8},
--       "kosdaq": {"value": 768, "change_pct": 1.2},
--       "usdkrw": 1325,
--       "vix": 18.4
--     },
--     "stocks": [
--       {
--         "ticker": "005930", "name": "삼성전자", "sector": "반도체",
--         "close": 73400, "change_pct": 3.2,
--         "zscore": 2.4, "price_anomaly": true,
--         "news_summary": "HBM 수주 확대 기대감..."
--       }
--     ],
--     "top_news": ["뉴스 제목 1", "뉴스 제목 2"]
--   }
-- ────────────────────────────────
create table public.notifications (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  report_type text not null check (
    report_type in ('KOR_PREMARKET', 'KOR_CLOSE', 'US_PREMARKET', 'US_CLOSE')
  ),
  is_read     boolean not null default false,
  payload     jsonb not null default '{}',
  created_at  timestamptz not null default now()
);

create index idx_notifications_user_created
  on public.notifications(user_id, created_at desc);

create index idx_notifications_user_unread
  on public.notifications(user_id, is_read)
  where is_read = false;

alter table public.notifications enable row level security;

-- 본인 알림만 조회 가능
create policy "본인 알림만 조회"
  on public.notifications for select
  using (auth.uid() = user_id);

-- 리포트 생성 파이프라인(service_role)만 삽입 가능
create policy "서비스 롤만 삽입"
  on public.notifications for insert
  with check (auth.role() = 'service_role');

-- 본인 알림만 읽음 처리 가능 (is_read 업데이트)
create policy "본인 알림 읽음 처리"
  on public.notifications for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);


-- ────────────────────────────────
-- market_snapshots
--   시장 스냅샷 (리포트 생성 시 저장, 모든 유저 공유)
--   리포트 생성 파이프라인이 적재 → 프론트엔드에서 직접 조회 가능
-- ────────────────────────────────
create table public.market_snapshots (
  id            uuid primary key default gen_random_uuid(),
  report_type   text not null check (
    report_type in ('KOR_PREMARKET', 'KOR_CLOSE', 'US_PREMARKET', 'US_CLOSE')
  ),
  snapshot_date date not null,
  payload       jsonb not null default '{}',
  created_at    timestamptz not null default now(),
  unique (report_type, snapshot_date)
);

create index idx_market_snapshots_type_date
  on public.market_snapshots(report_type, snapshot_date desc);

alter table public.market_snapshots enable row level security;

-- 로그인 사용자 누구나 조회 가능
create policy "시장 스냅샷 조회 허용"
  on public.market_snapshots for select
  using (auth.role() = 'authenticated');

-- 리포트 파이프라인(service_role)만 삽입/갱신 가능
create policy "서비스 롤만 upsert"
  on public.market_snapshots for all
  using (auth.role() = 'service_role');
