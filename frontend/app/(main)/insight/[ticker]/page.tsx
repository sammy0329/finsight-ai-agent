import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import InsightClient from './InsightClient'
import { type Segment } from '@/types'
import { fetchPrice } from '@/lib/yahoo'

interface Props {
  params: Promise<{ ticker: string }>
  searchParams: Promise<{ summary?: string }>
}

export default async function InsightPage({ params, searchParams }: Props) {
  const { ticker } = await params
  const { summary } = await searchParams
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles').select('segment').eq('user_id', user.id).single()
  if (!profile) redirect('/onboarding')

  // 종목 정보
  const { data: stock } = await supabase
    .from('stocks').select('ticker, name, market').eq('ticker', ticker).single()

  // Yahoo Finance 실시간 가격
  const market = stock?.market ?? ''
  const price = await fetchPrice(ticker, market)

  // watchlist 여부
  const { data: wl } = await supabase
    .from('watchlist').select('ticker').eq('user_id', user.id).eq('ticker', ticker).single()

  return (
    <InsightClient
      ticker={ticker}
      stockName={stock?.name ?? ticker}
      market={market}
      segment={profile.segment as Segment}
      price={price?.close ?? null}
      changePct={price?.change_pct ?? null}
      priceDate={price?.date ?? null}
      inWatchlist={!!wl}
      userId={user.id}
      reportSummary={summary ?? null}
    />
  )
}
