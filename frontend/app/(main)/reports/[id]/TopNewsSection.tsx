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
    <div className="flex flex-col gap-2 px-4">
      {normalized.map((news, i) => {
        const isOpen = expanded === i
        return (
          <div
            key={i}
            className="rounded-2xl overflow-hidden"
            style={{ background: '#1e1e1e' }}
          >
            {/* 클릭 영역 */}
            <button
              className="w-full text-left px-4 pt-3.5 pb-3"
              onClick={() => setExpanded(isOpen ? null : i)}
            >
              <p
                className="text-xs"
                style={{
                  color: '#ccc',
                  lineHeight: 1.75,
                  display: '-webkit-box',
                  WebkitLineClamp: isOpen ? undefined : 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: isOpen ? 'visible' : 'hidden',
                }}
              >
                {news.text}
              </p>
              <p className="mt-1.5 text-[10px]" style={{ color: '#444' }}>
                {isOpen ? '접기 ▲' : '더보기 ▼'}
              </p>
            </button>

            {/* 원문 링크 — 펼쳐졌을 때만 표시 */}
            {isOpen && (
              <div className="px-4 pb-3.5" style={{ borderTop: '1px solid #2a2a2a' }}>
                {news.url ? (
                  <a
                    href={news.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 mt-3 text-xs font-semibold"
                    style={{ color: '#60a5fa' }}
                  >
                    🔗 원문 뉴스 바로가기
                  </a>
                ) : (
                  <p className="mt-3 text-[11px]" style={{ color: '#444' }}>
                    원문 링크는 다음 파이프라인 실행 후 제공됩니다
                  </p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
