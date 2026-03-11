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
