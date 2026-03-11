'use client'

import { useState, useEffect, useCallback } from 'react'
import { createClient } from '@/lib/supabase/client'

interface StockResult {
  ticker: string
  name: string
  market: string
  close?: number
  change_pct?: number
}

export default function SearchPage() {
  const supabase = createClient()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<StockResult[]>([])
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)

  // 현재 watchlist 로드
  useEffect(() => {
    async function loadWatchlist() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return
      const { data } = await supabase
        .from('watchlist')
        .select('ticker')
        .eq('user_id', user.id)
      setWatchlist(new Set(data?.map(d => d.ticker) ?? []))
    }
    loadWatchlist()
  }, [supabase])

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoading(true)
    const res = await fetch(`/api/stocks/search?q=${encodeURIComponent(q)}`)
    const data = await res.json()
    setResults(data.stocks ?? [])
    setLoading(false)
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => search(query), 300)
    return () => clearTimeout(timer)
  }, [query, search])

  async function toggleWatchlist(stock: StockResult) {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    if (watchlist.has(stock.ticker)) {
      await supabase.from('watchlist').delete()
        .eq('user_id', user.id).eq('ticker', stock.ticker)
      setWatchlist(prev => { const s = new Set(prev); s.delete(stock.ticker); return s })
    } else {
      await supabase.from('watchlist').insert({
        user_id: user.id,
        ticker: stock.ticker,
        name: stock.name,
        market: stock.market,
      })
      setWatchlist(prev => { const s = new Set(Array.from(prev)); s.add(stock.ticker); return s })
    }
  }

  const kor = results.filter(r => r.market === 'KOSPI' || r.market === 'KOSDAQ')
  const us = results.filter(r => r.market === 'NASDAQ' || r.market === 'NYSE' || r.market === 'S&P500')

  return (
    <div style={{ color: '#f1f1f1' }}>
      {/* 헤더 */}
      <div className="px-5 pt-5 pb-3">
        <h1 className="text-xl font-bold mb-3">종목 검색</h1>
        <div className="flex items-center gap-2.5 px-3.5 py-3 rounded-xl"
          style={{ background: '#1e1e1e', border: '1px solid #2e2e2e' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="#555" strokeWidth="2"/>
            <path d="M20 20l-3-3" stroke="#555" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <input
            autoFocus
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="종목명 또는 코드 (예: 삼성, AAPL)"
            className="flex-1 bg-transparent text-sm outline-none"
            style={{ color: '#f1f1f1' }}
          />
          {query && (
            <button onClick={() => setQuery('')} style={{ color: '#555' }}>✕</button>
          )}
        </div>
      </div>

      {/* 결과 */}
      <div className="px-5">
        {loading && (
          <p className="text-sm text-center py-8" style={{ color: '#555' }}>검색 중...</p>
        )}

        {!loading && query && results.length === 0 && (
          <p className="text-sm text-center py-8" style={{ color: '#555' }}>검색 결과가 없습니다</p>
        )}

        {!loading && !query && (
          <p className="text-sm text-center py-8" style={{ color: '#555' }}>종목명이나 티커를 입력해보세요</p>
        )}

        {kor.length > 0 && (
          <>
            <p className="text-[11px] uppercase tracking-wider mb-1" style={{ color: '#555' }}>국내 · KRX</p>
            {kor.map((stock, i) => (
              <StockRow key={stock.ticker} stock={stock} added={watchlist.has(stock.ticker)}
                onToggle={() => toggleWatchlist(stock)} isLast={i === kor.length - 1} />
            ))}
          </>
        )}

        {us.length > 0 && (
          <>
            <p className="text-[11px] uppercase tracking-wider mb-1 mt-5" style={{ color: '#555' }}>해외 · NASDAQ/NYSE</p>
            {us.map((stock, i) => (
              <StockRow key={stock.ticker} stock={stock} added={watchlist.has(stock.ticker)}
                onToggle={() => toggleWatchlist(stock)} isLast={i === us.length - 1} />
            ))}
          </>
        )}
      </div>
    </div>
  )
}

function StockRow({ stock, added, onToggle, isLast }: {
  stock: StockResult
  added: boolean
  onToggle: () => void
  isLast: boolean
}) {
  const isUp = stock.change_pct != null ? stock.change_pct > 0 : null

  return (
    <>
      <div className="flex items-center justify-between py-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold"
            style={{ background: '#252525', color: '#888' }}>
            {stock.ticker.slice(0, 2)}
          </div>
          <div>
            <p className="text-sm font-medium">{stock.name}</p>
            <p className="text-[11px] mt-0.5" style={{ color: '#555' }}>{stock.ticker} · {stock.market}</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          {stock.close != null && (
            <div className="text-right">
              <p className="text-sm font-semibold">{stock.close.toLocaleString()}</p>
              {isUp !== null && (
                <p className="text-[11px]" style={{ color: isUp ? '#f87171' : '#60a5fa' }}>
                  {isUp ? '▲' : '▼'} {Math.abs(stock.change_pct!).toFixed(2)}%
                </p>
              )}
            </div>
          )}
          <button
            onClick={onToggle}
            className="px-2.5 py-1 rounded-lg text-xs font-semibold"
            style={added
              ? { background: '#1e1e1e', border: '1px solid #2a2a2a', color: '#444' }
              : { background: 'rgba(59,130,246,0.1)', border: '1px solid #3b82f6', color: '#3b82f6' }
            }
          >
            {added ? '추가됨' : '+ 추가'}
          </button>
        </div>
      </div>
      {!isLast && <div style={{ height: 1, background: '#222' }} />}
    </>
  )
}
