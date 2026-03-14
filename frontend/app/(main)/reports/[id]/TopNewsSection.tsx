interface NewsItem {
  text: string
  url: string
}

interface Props {
  items: (NewsItem | string)[]
}

export default function TopNewsSection({ items }: Props) {
  const normalized: NewsItem[] = items.map(item =>
    typeof item === 'string' ? { text: item, url: '' } : item
  )

  return (
    <div className="flex flex-col gap-2 px-4">
      {normalized.map((news, i) => (
        <div
          key={i}
          className="px-4 py-3.5 rounded-2xl"
          style={{ background: '#1e1e1e' }}
        >
          <p className="text-xs" style={{ color: '#ccc', lineHeight: 1.75 }}>
            {news.text}
          </p>
          {news.url && (
            <a
              href={news.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-[11px]"
              style={{ color: '#60a5fa' }}
            >
              🔗 원문 보기
            </a>
          )}
        </div>
      ))}
    </div>
  )
}
