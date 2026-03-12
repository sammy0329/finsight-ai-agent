import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { type Notification, REPORT_TYPE_CONFIG } from '@/types'

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)

  if (d.toDateString() === today.toDateString()) return '오늘'
  if (d.toDateString() === yesterday.toDateString()) return '어제'
  return d.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
}

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

export default async function ReportsPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: notifications } = await supabase
    .from('notifications')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(60)

  const items = (notifications ?? []) as Notification[]

  // 날짜별 그룹핑
  const grouped: Record<string, Notification[]> = {}
  items.forEach(item => {
    const key = formatDate(item.created_at)
    if (!grouped[key]) grouped[key] = []
    grouped[key]!.push(item)
  })

  // T-619: 빈 상태
  if (items.length === 0) {
    return (
      <div style={{ color: '#f1f1f1' }}>
        <div className="px-5 pt-5 pb-3">
          <h1 className="text-xl font-bold">리포트</h1>
          <p className="text-sm mt-0.5" style={{ color: '#555' }}>시장 브리프 & 마감 리포트</p>
        </div>
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <span className="text-4xl">🔔</span>
          <p className="text-sm font-medium" style={{ color: '#555' }}>아직 수신된 리포트가 없습니다</p>
          <p className="text-xs text-center px-8" style={{ color: '#444', lineHeight: 1.6 }}>
            관심 종목을 추가하면 한국·미국 시장의<br />
            장 전·마감 리포트를 자동으로 받아볼 수 있습니다
          </p>
          <Link
            href="/search"
            className="mt-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: '#1e1e1e', color: '#3b82f6', border: '1px solid #2e2e2e' }}
          >
            종목 추가하기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ color: '#f1f1f1' }}>
      <div className="px-5 pt-5 pb-3">
        <h1 className="text-xl font-bold">리포트</h1>
        <p className="text-sm mt-0.5" style={{ color: '#555' }}>
          {items.filter(n => !n.is_read).length > 0
            ? `미읽 ${items.filter(n => !n.is_read).length}건`
            : '모두 읽었습니다'}
        </p>
      </div>

      {Object.entries(grouped).map(([date, group]) => (
        <div key={date} className="mb-2">
          <p className="px-5 py-2 text-xs font-medium" style={{ color: '#555' }}>{date}</p>
          <div className="flex flex-col gap-2 px-4">
            {group.map(notif => {
              const cfg = REPORT_TYPE_CONFIG[notif.report_type]
              return (
                <Link
                  key={notif.id}
                  href={`/reports/${notif.id}`}
                  className="block p-4 rounded-2xl"
                  style={{
                    background: '#1e1e1e',
                    border: notif.is_read ? '1px solid transparent' : `1px solid ${cfg.color}33`,
                  }}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{cfg.icon}</span>
                      <span className="text-sm font-semibold">{cfg.label}</span>
                      {!notif.is_read && (
                        <span
                          className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{ background: cfg.color }}
                        />
                      )}
                    </div>
                    <span className="text-xs" style={{ color: '#555' }}>
                      {formatTime(notif.created_at)}
                    </span>
                  </div>
                  <p className="text-xs line-clamp-2" style={{ color: '#888', lineHeight: 1.6 }}>
                    {notif.payload.market_summary || '시장 요약을 불러오는 중...'}
                  </p>
                  {notif.payload.stocks.length > 0 && (
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {notif.payload.stocks.slice(0, 4).map(s => (
                        <span
                          key={s.ticker}
                          className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{
                            background: s.price_anomaly ? '#ef444420' : '#ffffff10',
                            color: s.price_anomaly ? '#f87171' : '#666',
                          }}
                        >
                          {s.name} {s.change_pct >= 0 ? '+' : ''}{s.change_pct.toFixed(1)}%
                        </span>
                      ))}
                    </div>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
