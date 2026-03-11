import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { type Segment } from '@/types'

const SEGMENT_COLOR: Record<Segment, string> = { A: '#3b82f6', B: '#ef4444', C: '#22c55e' }

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

export default async function HistoryPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles').select('segment').eq('user_id', user.id).single()

  const { data: history } = await supabase
    .from('insight_history')
    .select('id, ticker, stock_name, query, answer, created_at')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(50)

  const segment = (profile?.segment ?? 'A') as Segment
  const color = SEGMENT_COLOR[segment]

  // 날짜별 그룹핑
  const grouped: Record<string, typeof history> = {}
  history?.forEach(item => {
    const key = formatDate(item.created_at)
    if (!grouped[key]) grouped[key] = []
    grouped[key]!.push(item)
  })

  return (
    <div style={{ color: '#f1f1f1' }}>
      <div className="px-5 pt-5 pb-3">
        <h1 className="text-xl font-bold">인사이트 이력</h1>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <div className="text-center py-16">
          <p className="text-sm" style={{ color: '#555' }}>아직 인사이트 이력이 없습니다</p>
          <p className="text-xs mt-1" style={{ color: '#444' }}>관심 종목을 추가하고 인사이트를 생성해보세요</p>
        </div>
      ) : (
        Object.entries(grouped).map(([date, items]) => (
          <div key={date}>
            <p className="px-5 pt-3 pb-1.5 text-[11px]" style={{ color: '#555' }}>{date}</p>
            <div className="flex flex-col gap-2.5 px-4">
              {items!.map(item => (
                <Link key={item.id} href={`/insight/${item.ticker}`}
                  className="p-3.5 rounded-2xl block"
                  style={{ background: '#1e1e1e' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md"
                      style={{ background: '#252525', color: '#888' }}>
                      {item.stock_name}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                      style={{ background: `${color}26`, color, border: `1px solid ${color}4d` }}>
                      {segment}형
                    </span>
                    <span className="ml-auto text-[11px]" style={{ color: '#444' }}>
                      {formatTime(item.created_at)}
                    </span>
                  </div>
                  <p className="text-sm font-medium mb-1.5">{item.query}</p>
                  <p className="text-xs leading-relaxed line-clamp-2" style={{ color: '#555' }}>
                    {item.answer}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
