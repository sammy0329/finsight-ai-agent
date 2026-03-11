import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { SEGMENT_LABEL, SEGMENT_ICON, type Segment } from '@/types'

export default async function HomePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  // 프로필 조회
  const { data: profile } = await supabase
    .from('profiles')
    .select('segment')
    .eq('user_id', user.id)
    .single()

  if (!profile) redirect('/onboarding')

  const segment = profile.segment as Segment

  // watchlist + 최신 가격 조회
  const { data: watchlist } = await supabase
    .from('watchlist')
    .select('ticker, name, market, added_at')
    .eq('user_id', user.id)
    .order('added_at', { ascending: false })

  // 가격 데이터 조회
  const tickers = (watchlist ?? []).map(w => w.ticker)
  const priceMap: Record<string, { close: number; change_pct: number }> = {}
  if (tickers.length > 0) {
    const { data: prices } = await supabase
      .from('daily_prices')
      .select('ticker, close, change_pct, date')
      .in('ticker', tickers)
      .order('date', { ascending: false })

    // 종목별 최신 가격만
    prices?.forEach(p => {
      if (!priceMap[p.ticker]) priceMap[p.ticker] = { close: p.close, change_pct: p.change_pct }
    })
  }

  const segmentColor: Record<Segment, string> = { A: '#3b82f6', B: '#ef4444', C: '#22c55e' }
  const color = segmentColor[segment]

  return (
    <div style={{ color: '#f1f1f1' }}>
      {/* 헤더 */}
      <div className="flex items-start justify-between px-5 pt-5 pb-3">
        <div>
          <h1 className="text-lg font-bold">안녕하세요 👋</h1>
          <p className="text-sm mt-0.5" style={{ color: '#888' }}>오늘의 관심 종목 인사이트</p>
        </div>
        <span className="text-xs font-bold px-2 py-0.5 rounded-full"
          style={{ background: `${color}26`, color, border: `1px solid ${color}4d` }}>
          {SEGMENT_ICON[segment]} {segment}형 {SEGMENT_LABEL[segment]}
        </span>
      </div>

      {/* 시장 요약 배너 */}
      <div className="mx-4 mb-4 px-3.5 py-3 rounded-xl" style={{ background: '#1e1e1e', borderLeft: `3px solid ${color}` }}>
        <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: '#555' }}>오늘의 시장</p>
        <p className="text-xs" style={{ color: '#ccc' }}>
          KOSPI <span style={{ color: '#60a5fa' }}>▼ 0.8%</span> &nbsp;·&nbsp;
          NASDAQ <span style={{ color: '#60a5fa' }}>▼ 1.1%</span> &nbsp;·&nbsp;
          원/달러 1,342원
        </p>
      </div>

      {/* 관심 종목 섹션 */}
      <div className="flex items-center justify-between px-5 mb-3">
        <h2 className="text-sm font-semibold">관심 종목</h2>
        <Link href="/search" className="text-xs" style={{ color: '#3b82f6' }}>+ 추가</Link>
      </div>

      {watchlist && watchlist.length > 0 ? (
        <div className="flex flex-col gap-2.5 px-4">
          {watchlist.map(stock => {
            const price = priceMap[stock.ticker]
            const isUp = price ? price.change_pct > 0 : null
            return (
              <Link
                key={stock.ticker}
                href={`/insight/${stock.ticker}`}
                className="block p-4 rounded-2xl"
                style={{ background: '#1e1e1e' }}
              >
                <div className="flex justify-between items-start mb-2.5">
                  <div>
                    <h3 className="font-semibold text-sm">{stock.name}</h3>
                    <p className="text-xs mt-0.5" style={{ color: '#555' }}>{stock.ticker} · {stock.market}</p>
                  </div>
                  {price ? (
                    <div className="text-right">
                      <p className="font-bold text-sm">
                        {stock.market === 'NASDAQ' || stock.market === 'NYSE'
                          ? `$${price.close.toLocaleString()}`
                          : `${price.close.toLocaleString()}원`}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: isUp ? '#f87171' : '#60a5fa' }}>
                        {isUp ? '▲' : '▼'} {Math.abs(price.change_pct).toFixed(2)}%
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs" style={{ color: '#444' }}>가격 없음</p>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-xs truncate mr-2" style={{ color: '#666' }}>인사이트 보기 →</p>
                  <span className="text-xs px-2.5 py-1 rounded-lg flex-shrink-0"
                    style={{ background: `${color}1a`, color }}>
                    인사이트
                  </span>
                </div>
              </Link>
            )
          })}
        </div>
      ) : (
        <div className="mx-4">
          <Link
            href="/search"
            className="flex items-center justify-center gap-2 py-5 rounded-2xl text-sm"
            style={{ border: '1px dashed #2e2e2e', color: '#555' }}
          >
            <span className="text-lg">+</span>
            관심 종목을 추가해보세요
          </Link>
        </div>
      )}
    </div>
  )
}
