export type Segment = 'A' | 'B' | 'C'
export type Market = 'KRX' | 'NASDAQ' | 'NYSE' | 'S&P500'

export interface Profile {
  user_id: string
  segment: Segment
  created_at: string
}

export interface Stock {
  ticker: string
  name: string
  market: Market
}

export interface DailyPrice {
  ticker: string
  date: string
  close: number
  change_pct: number
}

export interface WatchlistItem extends Stock {
  added_at: string
  close?: number
  change_pct?: number
}

export interface InsightHistory {
  id: string
  user_id: string
  ticker: string
  stock_name: string
  query: string
  answer: string
  sources: string[]
  created_at: string
}

export type ReportType = 'KOR_PREMARKET' | 'KOR_CLOSE' | 'US_PREMARKET' | 'US_CLOSE'

export interface ReportMarketIndex {
  value: number
  change_pct: number
}

export interface ReportMarket {
  kospi?: ReportMarketIndex
  kosdaq?: ReportMarketIndex
  sp500?: ReportMarketIndex
  nasdaq?: ReportMarketIndex
  dow?: ReportMarketIndex
  usdkrw?: number
  eurkrw?: number
}

export interface ReportStock {
  ticker: string
  name: string
  sector: string
  close: number
  change_pct: number
  zscore: number | null
  price_anomaly: boolean
  news_summary: string
}

export interface ReportPayload {
  market_summary: string
  market: ReportMarket
  stocks: ReportStock[]
  top_news: string[]
}

export interface Notification {
  id: string
  user_id: string
  report_type: ReportType
  is_read: boolean
  payload: ReportPayload
  created_at: string
}

export const REPORT_TYPE_CONFIG: Record<ReportType, { label: string; icon: string; color: string }> = {
  KOR_PREMARKET: { label: '한국 장 전', icon: '🌅', color: '#f59e0b' },
  KOR_CLOSE:     { label: '한국 장 마감', icon: '🌆', color: '#3b82f6' },
  US_PREMARKET:  { label: '미국 장 전', icon: '🌃', color: '#8b5cf6' },
  US_CLOSE:      { label: '미국 장 마감', icon: '☀️', color: '#22c55e' },
}

export const SEGMENT_LABEL: Record<Segment, string> = {
  A: '안전추구형',
  B: '위험감수형',
  C: '가치투자형',
}

export const SEGMENT_COLOR: Record<Segment, string> = {
  A: '#3b82f6',
  B: '#ef4444',
  C: '#22c55e',
}

export const SEGMENT_ICON: Record<Segment, string> = {
  A: '🛡️',
  B: '🚀',
  C: '🔍',
}
