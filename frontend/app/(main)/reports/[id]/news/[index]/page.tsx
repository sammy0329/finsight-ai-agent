import { createClient } from '@/lib/supabase/server'
import { notFound, redirect } from 'next/navigation'
import Link from 'next/link'
import { type Notification } from '@/types'

interface Props {
  params: Promise<{ id: string; index: string }>
}

export default async function NewsDetailPage({ params }: Props) {
  const { id, index } = await params
  const idx = parseInt(index, 10)

  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: notif } = await supabase
    .from('notifications')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single()

  if (!notif) notFound()

  const n = notif as Notification
  const rawItem = n.payload.top_news[idx]
  if (rawItem === undefined) notFound()

  const news = typeof rawItem === 'string'
    ? { text: rawItem, url: '' }
    : rawItem

  return (
    <div style={{ color: '#f1f1f1', minHeight: '100dvh', background: '#141414' }}>
      {/* 상단 바 */}
      <div className="flex items-center gap-3 px-5 pt-4 pb-3" style={{ borderBottom: '1px solid #1e1e1e' }}>
        <Link
          href={`/reports/${id}`}
          className="w-8 h-8 rounded-xl flex items-center justify-center text-sm"
          style={{ background: '#1e1e1e' }}
        >
          ←
        </Link>
        <h1 className="text-base font-bold flex-1">뉴스 상세</h1>
      </div>

      {/* 뉴스 본문 */}
      <div className="px-5 py-5">
        <p className="text-sm leading-relaxed" style={{ color: '#ccc', lineHeight: 1.8 }}>
          {news.text}
        </p>
      </div>

      {/* 원문 바로가기 */}
      {news.url && (
        <div className="px-5">
          <a
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3.5 rounded-2xl text-sm font-semibold"
            style={{ background: '#1e3a5f', color: '#60a5fa', border: '1px solid #1e4a7a' }}
          >
            🔗 원문 뉴스 바로가기
          </a>
        </div>
      )}
    </div>
  )
}
