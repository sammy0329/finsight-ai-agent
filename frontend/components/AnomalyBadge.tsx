'use client'

import { useEffect, useState } from 'react'

interface AnomalyData {
  is_anomaly: boolean
  zscore: number | null
  direction: '급등' | '급락' | null
  latest_return_pct: number | null
  message: string
}

export default function AnomalyBadge({ ticker }: { ticker: string }) {
  const [data, setData] = useState<AnomalyData | null>(null)

  useEffect(() => {
    fetch(`/api/stocks/anomaly/${ticker}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => null)
  }, [ticker])

  if (!data?.is_anomaly) return null

  const isUp = data.direction === '급등'

  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
      style={{
        background: isUp ? 'rgba(248,113,113,0.15)' : 'rgba(96,165,250,0.15)',
        color: isUp ? '#f87171' : '#60a5fa',
        border: `1px solid ${isUp ? '#f8717140' : '#60a5fa40'}`,
      }}
    >
      ⚡ {data.direction}
    </span>
  )
}
