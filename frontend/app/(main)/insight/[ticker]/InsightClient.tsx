'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { type Segment, SEGMENT_LABEL, SEGMENT_ICON } from '@/types'
import FinancialsCard from '@/components/FinancialsCard'

const SEGMENT_COLOR: Record<Segment, string> = { A: '#3b82f6', B: '#ef4444', C: '#22c55e' }

const SUGGESTED_QUESTIONS: Record<Segment, string[]> = {
  A: [
    '최근 이 종목 관련 주요 뉴스는 무엇인가요?',
    '실적 발표나 배당 관련 최신 소식이 있나요?',
    '업계에서 주목할 만한 리스크 이슈가 있나요?',
  ],
  B: [
    '최근 급등락에 영향을 준 뉴스가 있나요?',
    '이 종목이 속한 섹터의 최신 동향은 어떤가요?',
    '경쟁사 대비 최근 이슈나 차별점이 있나요?',
  ],
  C: [
    '최근 실적 발표 내용과 시장 반응은 어땠나요?',
    '이 기업의 사업 구조나 주요 수익원은 무엇인가요?',
    '업황 변화나 규제 이슈 중 주목할 내용이 있나요?',
  ],
}

interface Props {
  ticker: string
  stockName: string
  market: string
  segment: Segment
  price: number | null
  changePct: number | null
  priceDate: string | null
  inWatchlist: boolean
  userId: string
  reportSummary: string | null
  reportNewsUrl: string | null
}

export default function InsightClient({
  ticker, stockName, market, segment,
  price, changePct, priceDate,
  inWatchlist: initialInWatchlist, userId,
  reportSummary, reportNewsUrl,
}: Props) {
  const router = useRouter()
  const supabase = createClient()
  const color = SEGMENT_COLOR[segment]
  const isUp = changePct != null ? changePct > 0 : null

  const [insight, setInsight] = useState('')
  const [sources, setSources] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [inWatchlist, setInWatchlist] = useState(initialInWatchlist)
  const [anomaly, setAnomaly] = useState<{
    is_anomaly: boolean
    zscore: number | null
    direction: '급등' | '급락' | null
    latest_return_pct: number | null
    message: string
  } | null>(null)

  useEffect(() => {
    fetch(`/api/stocks/anomaly/${ticker}`)
      .then(r => r.json())
      .then(setAnomaly)
      .catch(() => null)
  }, [ticker])

  async function fetchInsight(q: string) {
    if (!q.trim()) return
    setLoading(true)
    setInsight('')
    setSources([])

    try {
      const res = await fetch('/api/insight', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, query: q, segment }),
      })

      if (!res.ok) throw new Error('API 오류')

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        // SSE 파싱
        chunk.split('\n').forEach(line => {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trimEnd()
            if (data === '[DONE]') return
            if (data.startsWith('[SOURCES]')) {
              try { setSources(JSON.parse(data.slice(9))) } catch { /* noop */ }
            } else {
              // <br> → 실제 개행으로 복원
              fullText += data.replace(/<br>/g, '\n')
              setInsight(fullText)
            }
          }
        })
      }

      // 이력 저장
      await supabase.from('insight_history').insert({
        user_id: userId,
        ticker,
        stock_name: stockName,
        query: q,
        answer: fullText,
        sources,
      })
    } catch {
      setInsight('인사이트를 불러오는 데 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setLoading(false)
    }
  }

  async function toggleWatchlist() {
    if (inWatchlist) {
      await supabase.from('watchlist').delete().eq('user_id', userId).eq('ticker', ticker)
    } else {
      await supabase.from('watchlist').insert({ user_id: userId, ticker, name: stockName, market })
    }
    setInWatchlist(!inWatchlist)
  }

  return (
    <div style={{ color: '#f1f1f1' }}>
      {/* 상단 바 */}
      <div className="flex items-center gap-3 px-5 pt-4 pb-2">
        <button onClick={() => router.back()}
          className="w-8 h-8 rounded-xl flex items-center justify-center text-sm"
          style={{ background: '#1e1e1e' }}>
          ←
        </button>
        <h1 className="text-base font-bold flex-1">{stockName}</h1>
        <button
          onClick={toggleWatchlist}
          className="text-xs px-2.5 py-1 rounded-lg"
          style={inWatchlist
            ? { background: '#1e1e1e', border: '1px solid #2a2a2a', color: '#555' }
            : { background: `${color}1a`, border: `1px solid ${color}4d`, color }}
        >
          {inWatchlist ? '★ 등록됨' : '☆ 추가'}
        </button>
        <span className="text-xs font-bold px-2 py-0.5 rounded-full"
          style={{ background: `${color}26`, color, border: `1px solid ${color}4d` }}>
          {segment}형
        </span>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-hide px-4 pb-4">
        {/* 가격 카드 */}
        <div className="p-4 rounded-2xl mb-3.5" style={{ background: '#1e1e1e' }}>
          <div className="flex justify-between items-start mb-2.5">
            <div>
              <p className="text-[11px] mb-1" style={{ color: '#555' }}>{ticker} · {market} · 전일 종가</p>
              <p className="text-3xl font-bold">
                {price != null
                  ? (market === 'NASDAQ' || market === 'NYSE'
                    ? `$${price.toLocaleString()}`
                    : `${price.toLocaleString()}원`)
                  : '—'}
              </p>
            </div>
            {isUp !== null && (
              <div className="px-2.5 py-1.5 rounded-lg text-sm font-bold"
                style={isUp
                  ? { background: 'rgba(248,113,113,0.15)', color: '#f87171' }
                  : { background: 'rgba(96,165,250,0.15)', color: '#60a5fa' }}>
                {isUp ? '▲' : '▼'} {Math.abs(changePct!).toFixed(2)}%
              </div>
            )}
          </div>
          <div className="flex gap-4 text-[11px]" style={{ color: '#555' }}>
            {changePct != null && (
              <span>전일 대비 <span style={{ color: isUp ? '#f87171' : '#60a5fa' }}>
                {isUp ? '+' : ''}{changePct.toFixed(2)}%
              </span></span>
            )}
            {priceDate && <span>기준일 {priceDate}</span>}
          </div>
        </div>

        {/* 재무지표 카드 */}
        <FinancialsCard ticker={ticker} />

        {/* 이상 감지 카드 */}
        {anomaly?.is_anomaly && (
          <div
            className="mb-3.5 p-3.5 rounded-xl flex items-start gap-3"
            style={{
              background: anomaly.direction === '급등'
                ? 'rgba(248,113,113,0.08)'
                : 'rgba(96,165,250,0.08)',
              border: `1px solid ${anomaly.direction === '급등' ? '#f8717130' : '#60a5fa30'}`,
            }}
          >
            <span className="text-lg leading-none">⚡</span>
            <div className="flex-1">
              <p className="text-xs font-bold mb-0.5"
                style={{ color: anomaly.direction === '급등' ? '#f87171' : '#60a5fa' }}>
                오늘 {anomaly.direction} 감지
              </p>
              <p className="text-[11px]" style={{ color: '#999' }}>
                오늘 수익률 {anomaly.latest_return_pct != null
                  ? `${anomaly.latest_return_pct > 0 ? '+' : ''}${anomaly.latest_return_pct.toFixed(2)}%`
                  : '—'
                }로 통계적 이상 변동입니다 (Z-score: {anomaly.zscore?.toFixed(2)})
              </p>
              <button
                className="mt-2 text-[11px] font-semibold underline"
                style={{ color: anomaly.direction === '급등' ? '#f87171' : '#60a5fa' }}
                onClick={() => {
                  const q = `오늘 ${stockName} ${anomaly.direction}에 영향을 준 뉴스나 이슈가 있나요?`
                  setQuery(q)
                  fetchInsight(q)
                }}
              >
                원인 분석하기 →
              </button>
            </div>
          </div>
        )}

        {/* 리포트 뉴스 요약 */}
        {reportSummary && !insight && !loading && (
          <div className="mb-3.5 p-3.5 rounded-xl" style={{ background: '#1a1a1a', border: '1px solid #2a2a2a' }}>
            <p className="text-[11px] font-semibold mb-1.5" style={{ color: '#888' }}>📰 리포트 뉴스 요약</p>
            <p className="text-xs leading-relaxed" style={{ color: '#bbb' }}>{reportSummary}</p>
            {reportNewsUrl && (
              <a
                href={reportNewsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 flex items-center gap-1 text-[11px]"
                style={{ color: '#60a5fa' }}
              >
                <span style={{ fontSize: 10 }}>🔗</span> 참고 기사 원문 보기
              </a>
            )}
            <button
              className="mt-2.5 text-[11px] font-semibold"
              style={{ color: '#a78bfa' }}
              onClick={() => {
                const q = `${stockName} 관련 최신 뉴스와 주가 영향을 분석해줘`
                setQuery(q)
                fetchInsight(q)
              }}
            >
              AI로 더 분석하기 →
            </button>
          </div>
        )}

        {/* AI 인사이트 */}
        {insight ? (
          <div className="mb-3.5">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-sm font-semibold">AI 인사이트</h2>
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.2)' }}>
                RAG
              </span>
              <span className="text-[11px] ml-auto" style={{ color: '#555' }}>{SEGMENT_ICON[segment]} {SEGMENT_LABEL[segment]} 관점</span>
            </div>
            <div className="p-3.5 rounded-xl text-sm leading-relaxed whitespace-pre-wrap" style={{ background: '#1a1a1a', color: '#ccc' }}>
              {insight}
              {loading && <span className="cursor-blink" />}
            </div>
            {sources.length > 0 && (
              <div className="mt-2.5">
                <p className="text-[11px] mb-1.5" style={{ color: '#555' }}>근거 뉴스 출처</p>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((src, i) => (
                    <span key={i} className="text-[11px] px-2.5 py-1 rounded-full"
                      style={{ background: '#222', border: '1px solid #2e2e2e', color: '#777' }}>
                      {src}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : !loading && (
          <div className="mb-3.5">
            <h2 className="text-sm font-semibold mb-2">질문 예시</h2>
            <div className="flex flex-col gap-2">
              {SUGGESTED_QUESTIONS[segment].map(q => (
                <button key={q} onClick={() => { setQuery(q); fetchInsight(q) }}
                  className="text-left text-xs px-3 py-2.5 rounded-xl"
                  style={{ background: '#1a1a1a', border: '1px solid #222', color: '#777' }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && !insight && (
          <div className="text-center py-6">
            <p className="text-sm" style={{ color: '#555' }}>인사이트 생성 중...</p>
          </div>
        )}
      </div>

      {/* 질문 입력창 */}
      <div className="px-4 py-3" style={{ borderTop: '1px solid #1e1e1e', background: '#141414' }}>
        <p className="text-[11px] mb-1.5" style={{ color: '#555' }}>이 종목에 대해 더 물어보기</p>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { fetchInsight(query); setQuery('') } }}
            placeholder={`예: ${SUGGESTED_QUESTIONS[segment][0]}`}
            className="flex-1 px-3.5 py-2.5 rounded-xl text-sm outline-none"
            style={{ background: '#1e1e1e', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
          />
          <button
            onClick={() => { fetchInsight(query); setQuery('') }}
            disabled={!query.trim() || loading}
            className="w-10 h-10 rounded-xl flex items-center justify-center disabled:opacity-40 flex-shrink-0"
            style={{ background: '#3b82f6' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
