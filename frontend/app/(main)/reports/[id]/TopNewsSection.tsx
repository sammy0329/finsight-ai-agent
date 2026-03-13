'use client'

import { useState } from 'react'

interface NewsItem {
  text: string
  url: string
}

interface Props {
  items: (NewsItem | string)[]
}

export default function TopNewsSection({ items }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null)

  const normalized: NewsItem[] = items.map(item =>
    typeof item === 'string' ? { text: item, url: '' } : item
  )

  return (
    <div className="flex flex-col gap-1.5 px-4">
      {normalized.map((news, i) => {
        const isOpen = expanded === i
        return (
          <div
            key={i}
            className="rounded-xl text-xs cursor-pointer"
            style={{ background: '#1e1e1e' }}
            onClick={() => setExpanded(isOpen ? null : i)}
          >
            <p
              className="px-4 py-3"
              style={{
                color: '#aaa',
                lineHeight: 1.6,
                display: '-webkit-box',
                WebkitLineClamp: isOpen ? undefined : 3,
                WebkitBoxOrient: 'vertical',
                overflow: isOpen ? 'visible' : 'hidden',
              }}
            >
              {news.text}
            </p>
            {isOpen && (
              <div className="px-4 pb-3 flex items-center justify-between">
                <span className="text-[10px]" style={{ color: '#444' }}>
                  {isOpen ? '▲ 접기' : '▼ 더보기'}
                </span>
                {news.url && (
                  <a
                    href={news.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="text-[11px] font-semibold px-2.5 py-1 rounded-lg"
                    style={{ background: '#252525', color: '#60a5fa' }}
                  >
                    원문 뉴스 바로가기 →
                  </a>
                )}
              </div>
            )}
            {!isOpen && (
              <p className="px-4 pb-2 text-[10px]" style={{ color: '#444' }}>더보기 ▼</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
