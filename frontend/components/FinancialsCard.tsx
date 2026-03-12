'use client'

import { useEffect, useState } from 'react'

interface FinancialMetrics {
  ticker: string
  period: string
  per: number | null
  pbr: number | null
  roe: number | null
  eps: number | null
  revenue: number | null
  op_income: number | null
  net_income: number | null
}

function fmtMultiple(val: number | null) {
  if (val == null) return '—'
  return `${val.toFixed(1)}x`
}

function fmtPct(val: number | null) {
  if (val == null) return '—'
  return `${(val * 100).toFixed(1)}%`
}

function fmtWon(val: number | null) {
  if (val == null) return '—'
  const abs = Math.abs(val)
  if (abs >= 1e12) return `${(val / 1e12).toFixed(1)}조`
  if (abs >= 1e8) return `${(val / 1e8).toFixed(0)}억`
  return val.toLocaleString()
}

export default function FinancialsCard({ ticker }: { ticker: string }) {
  const [data, setData] = useState<FinancialMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/stocks/financials/${ticker}`)
      .then(r => r.json())
      .then(setData)
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [ticker])

  if (loading || !data) return null

  const metrics = [
    { label: 'PER', value: fmtMultiple(data.per) },
    { label: 'PBR', value: fmtMultiple(data.pbr) },
    { label: 'ROE', value: fmtPct(data.roe) },
  ]

  return (
    <div className="mb-3.5 p-3.5 rounded-xl" style={{ background: '#1e1e1e' }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold" style={{ color: '#aaa' }}>재무지표</p>
        <span className="text-[10px] px-1.5 py-0.5 rounded"
          style={{ background: '#2a2a2a', color: '#666' }}>
          {data.period}
        </span>
      </div>

      {/* PER / PBR / ROE */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {metrics.map(({ label, value }) => (
          <div key={label} className="text-center py-2 rounded-lg" style={{ background: '#141414' }}>
            <p className="text-[10px] mb-1" style={{ color: '#555' }}>{label}</p>
            <p className="text-sm font-bold" style={{ color: '#e0e0e0' }}>{value}</p>
          </div>
        ))}
      </div>

      {/* 매출 / 영업이익 */}
      <div className="flex gap-2">
        <div className="flex-1 px-3 py-2 rounded-lg" style={{ background: '#141414' }}>
          <p className="text-[10px] mb-0.5" style={{ color: '#555' }}>매출액</p>
          <p className="text-xs font-semibold" style={{ color: '#e0e0e0' }}>
            {fmtWon(data.revenue)}
          </p>
        </div>
        <div className="flex-1 px-3 py-2 rounded-lg" style={{ background: '#141414' }}>
          <p className="text-[10px] mb-0.5" style={{ color: '#555' }}>영업이익</p>
          <p className="text-xs font-semibold" style={{ color: '#e0e0e0' }}>
            {fmtWon(data.op_income)}
          </p>
        </div>
      </div>
    </div>
  )
}
