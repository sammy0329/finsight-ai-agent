import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get('q')?.trim()
  if (!q || q.length < 1) {
    return NextResponse.json({ stocks: [] })
  }

  const supabase = await createClient()

  const { data, error } = await supabase
    .from('stocks')
    .select('ticker, name, market')
    .or(`name.ilike.%${q}%,ticker.ilike.%${q}%`)
    .limit(20)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // 가격 데이터 조회
  const tickers = (data ?? []).map(s => s.ticker)
  const priceMap: Record<string, { close: number; change_pct: number }> = {}

  if (tickers.length > 0) {
    const { data: prices } = await supabase
      .from('daily_prices')
      .select('ticker, close, change_pct, date')
      .in('ticker', tickers)
      .order('date', { ascending: false })

    prices?.forEach(p => {
      if (!priceMap[p.ticker]) {
        priceMap[p.ticker] = { close: p.close, change_pct: p.change_pct }
      }
    })
  }

  const stocks = (data ?? []).map(s => ({
    ...s,
    close: priceMap[s.ticker]?.close,
    change_pct: priceMap[s.ticker]?.change_pct,
  }))

  return NextResponse.json({ stocks })
}
