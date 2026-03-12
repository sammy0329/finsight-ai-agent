-- T-605: market_indices / fx_rates 테이블 스키마

-- market_indices table
create table public.market_indices (
  id         bigserial primary key,
  symbol     text not null,
  name       text not null,
  date       date not null,
  close      numeric(12, 2) not null,
  change_pct numeric(6, 2),
  market     text not null,
  unique (symbol, date)
);
alter table public.market_indices enable row level security;
create policy "시장 지수 조회 허용" on public.market_indices
  for select using (true);

-- fx_rates table
create table public.fx_rates (
  id    bigserial primary key,
  pair  text not null,
  date  date not null,
  rate  numeric(12, 4) not null,
  unique (pair, date)
);
alter table public.fx_rates enable row level security;
create policy "환율 조회 허용" on public.fx_rates
  for select using (true);
