import Link from 'next/link'

interface NewsItem {
  text: string
  url: string
}

interface Props {
  items: (NewsItem | string)[]
  reportId: string
}

export default function TopNewsSection({ items, reportId }: Props) {
  const normalized: NewsItem[] = items.map(item =>
    typeof item === 'string' ? { text: item, url: '' } : item
  )

  return (
    <div className="flex flex-col gap-1.5 px-4">
      {normalized.map((news, i) => (
        <Link
          key={i}
          href={`/reports/${reportId}/news/${i}`}
          className="px-4 py-3 rounded-xl text-xs block"
          style={{ background: '#1e1e1e', color: '#aaa', lineHeight: 1.6 }}
        >
          <p className="line-clamp-3">{news.text}</p>
          <p className="mt-1.5 text-[10px]" style={{ color: '#444' }}>
            자세히 보기{news.url ? ' · 원문 있음' : ''} →
          </p>
        </Link>
      ))}
    </div>
  )
}
