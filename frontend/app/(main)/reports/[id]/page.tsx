import { createClient } from '@/lib/supabase/server'
import { notFound, redirect } from 'next/navigation'
import Link from 'next/link'
import { type Notification, type ReportMarket, REPORT_TYPE_CONFIG } from '@/types'

function IndexRow({ label, value, changePct }: { label: string; value: number; changePct?: number }) {
  const isUp = (changePct ?? 0) >= 0
  return (
    <div className="flex items-center justify-between py-2.5" style={{ borderBottom: '1px solid #252525' }}>
      <span className="text-sm" style={{ color: '#aaa' }}>{label}</span>
      <div className="text-right">
        <span className="text-sm font-semibold">
          {value.toLocaleString('ko-KR', { maximumFractionDigits: 2 })}
        </span>
        {changePct !== undefined && (
          <span className="text-xs ml-2" style={{ color: isUp ? '#f87171' : '#60a5fa' }}>
            {isUp ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  )
}

function MarketSection({ market }: { market: ReportMarket }) {
  const rows: Array<{ label: string; value: number; changePct?: number }> = []

  if (market.kospi)  rows.push({ label: 'KOSPI',   value: market.kospi.value,   changePct: market.kospi.change_pct })
  if (market.kosdaq) rows.push({ label: 'KOSDAQ',  value: market.kosdaq.value,  changePct: market.kosdaq.change_pct })
  if (market.sp500)  rows.push({ label: 'S&P500',  value: market.sp500.value,   changePct: market.sp500.change_pct })
  if (market.nasdaq) rows.push({ label: 'NASDAQ',  value: market.nasdaq.value,  changePct: market.nasdaq.change_pct })
  if (market.dow)    rows.push({ label: 'DOW',     value: market.dow.value,     changePct: market.dow.change_pct })
  if (market.usdkrw) rows.push({ label: '원/달러', value: market.usdkrw })

  if (rows.length === 0) return null

  return (
    <div className="mx-4 mb-4 p-4 rounded-2xl" style={{ background: '#1e1e1e' }}>
      <p className="text-xs font-medium mb-2" style={{ color: '#555' }}>시장 지수</p>
      {rows.map(r => (
        <IndexRow key={r.label} label={r.label} value={r.value} changePct={r.changePct} />
      ))}
    </div>
  )
}

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data, error } = await supabase
    .from('notifications')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (error || !data) notFound()

  const notif = data as Notification
  const cfg = REPORT_TYPE_CONFIG[notif.report_type]
  const { payload } = notif

  // T-618: 읽음 처리 (미읽 상태일 때만 업데이트)
  if (!notif.is_read) {
    await supabase
      .from('notifications')
      .update({ is_read: true })
      .eq('id', id)
      .eq('user_id', user.id)
  }

  const reportDate = new Date(notif.created_at).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })
  const reportTime = new Date(notif.created_at).toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div style={{ color: '#f1f1f1' }}>
      {/* 헤더 */}
      <div
        className="px-5 pt-5 pb-5"
        style={{
          background: `linear-gradient(to bottom, ${cfg.color}18, transparent)`,
          borderBottom: `1px solid ${cfg.color}33`,
        }}
      >
        <Link href="/reports" className="flex items-center gap-1.5 mb-4 text-xs" style={{ color: '#555' }}>
          <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
            <path d="M15 18l-6-6 6-6" stroke="#555" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          리포트 목록
        </Link>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-2xl">{cfg.icon}</span>
          <h1 className="text-lg font-bold">{cfg.label}</h1>
        </div>
        <p className="text-xs" style={{ color: '#555' }}>
          {reportDate} · {reportTime}
        </p>
      </div>

      {/* 시장 요약 */}
      {payload.market_summary && (
        <div className="mx-4 mt-4 mb-4 p-4 rounded-2xl" style={{ background: '#1e1e1e', borderLeft: `3px solid ${cfg.color}` }}>
          <p className="text-xs font-medium mb-2" style={{ color: '#555' }}>시장 요약</p>
          <p className="text-sm" style={{ color: '#ccc', lineHeight: 1.7 }}>{payload.market_summary}</p>
        </div>
      )}

      {/* 시장 지수 */}
      <MarketSection market={payload.market} />

      {/* 관심 종목 */}
      {payload.stocks.length > 0 && (
        <div className="mb-4">
          <p className="px-5 py-2 text-xs font-medium" style={{ color: '#555' }}>관심 종목</p>
          <div className="flex flex-col gap-2 px-4">
            {payload.stocks.map(stock => {
              const isUp = stock.change_pct >= 0
              return (
                <Link
                  key={stock.ticker}
                  href={`/insight/${encodeURIComponent(stock.ticker)}`}
                  className="p-3.5 rounded-2xl block"
                  style={{ background: '#1e1e1e' }}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-semibold">{stock.name || stock.ticker}</span>
                        {stock.price_anomaly && (
                          <span
                            className="text-[9px] px-1.5 py-0.5 rounded font-bold"
                            style={{ background: '#ef444420', color: '#f87171' }}
                          >
                            {(stock.zscore ?? 0) > 0 ? '급등' : '급락'}
                          </span>
                        )}
                      </div>
                      <p className="text-xs mt-0.5" style={{ color: '#555' }}>
                        {stock.ticker} {stock.sector ? `· ${stock.sector}` : ''}
                      </p>
                    </div>
                    <div className="text-right">
                      {stock.close > 0 && (
                        <>
                          <p className="text-sm font-bold">
                            {stock.close.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}
                          </p>
                          <p className="text-xs mt-0.5" style={{ color: isUp ? '#f87171' : '#60a5fa' }}>
                            {isUp ? '▲' : '▼'} {Math.abs(stock.change_pct).toFixed(2)}%
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                  {stock.news_summary && (
                    <p className="text-xs mt-1 line-clamp-3" style={{ color: '#666', lineHeight: 1.6 }}>
                      {stock.news_summary}
                    </p>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      )}

      {/* 주요 뉴스 */}
      {payload.top_news.length > 0 && (
        <div className="mb-8">
          <p className="px-5 py-2 text-xs font-medium" style={{ color: '#555' }}>주요 뉴스</p>
          <div className="flex flex-col gap-1.5 px-4">
            {payload.top_news.map((news, i) => (
              <div
                key={i}
                className="px-4 py-3 rounded-xl text-xs"
                style={{ background: '#1e1e1e', color: '#aaa', lineHeight: 1.6 }}
              >
                {news}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
