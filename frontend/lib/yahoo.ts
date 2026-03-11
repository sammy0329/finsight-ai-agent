export interface PriceData {
  ticker: string
  close: number
  change_pct: number
  prev_close: number
  date: string
}

/**
 * Yahoo Finance 티커 변환
 * KOSPI: 005930 → 005930.KS
 * KOSDAQ: 042700 → 042700.KQ
 * US/S&P500: AAPL → AAPL (그대로)
 */
function toYahooTicker(ticker: string, market: string): string {
  if (market === 'KOSPI') return `${ticker}.KS`
  if (market === 'KOSDAQ') return `${ticker}.KQ`
  return ticker
}

/**
 * 단일 종목 가격 조회
 */
export async function fetchPrice(
  ticker: string,
  market: string
): Promise<PriceData | null> {
  const yahooTicker = toYahooTicker(ticker, market)
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${yahooTicker}?interval=1d&range=5d`

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      next: { revalidate: 3600 }, // 1시간 캐시
    })
    if (!res.ok) return null

    const json = await res.json()
    const result = json?.chart?.result?.[0]
    if (!result) return null

    const closes: number[] = result.indicators?.quote?.[0]?.close ?? []
    const timestamps: number[] = result.timestamp ?? []

    // null 제거 후 최근 2개
    const valid = closes
      .map((c, i) => ({ close: c, ts: timestamps[i] }))
      .filter(d => d.close != null)

    if (valid.length < 1) return null

    const latest = valid[valid.length - 1]
    const prev = valid.length >= 2 ? valid[valid.length - 2] : null

    const change_pct =
      prev && prev.close > 0
        ? parseFloat(((latest.close - prev.close) / prev.close * 100).toFixed(2))
        : 0

    return {
      ticker,
      close: latest.close,
      prev_close: prev?.close ?? latest.close,
      change_pct,
      date: new Date(latest.ts * 1000).toISOString().slice(0, 10),
    }
  } catch {
    return null
  }
}

export interface MarketSummary {
  kospi: { value: number; change_pct: number } | null
  nasdaq: { value: number; change_pct: number } | null
  usdkrw: number | null
}

/**
 * 시장 요약 (KOSPI, NASDAQ, 원/달러) 실시간 조회
 */
export async function fetchMarketSummary(): Promise<MarketSummary> {
  const INDICES = [
    { key: 'kospi', ticker: '%5EKS11' },   // ^KS11
    { key: 'nasdaq', ticker: '%5EIXIC' },  // ^IXIC
    { key: 'usdkrw', ticker: 'KRW%3DX' }, // KRW=X
  ]

  const results = await Promise.allSettled(
    INDICES.map(({ ticker }) =>
      fetch(
        `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=5d`,
        { headers: { 'User-Agent': 'Mozilla/5.0' }, next: { revalidate: 1800 } }
      ).then(r => r.ok ? r.json() : null)
    )
  )

  function parse(json: unknown) {
    if (!json) return null
    type YahooResult = { indicators?: { quote?: { close?: number[] }[] }; timestamp?: number[] }
    type YahooJson = { chart?: { result?: YahooResult[] } }
    const result = (json as YahooJson)?.chart?.result?.[0]
    if (!result) return null
    const closes: number[] = result.indicators?.quote?.[0]?.close ?? []
    const valid = closes.filter(c => c != null)
    if (valid.length < 2) return null
    const latest = valid[valid.length - 1]
    const prev = valid[valid.length - 2]
    return { value: latest, change_pct: parseFloat(((latest - prev) / prev * 100).toFixed(2)) }
  }

  const [kospiRes, nasdaqRes, usdkrwRes] = results.map(r =>
    r.status === 'fulfilled' ? parse(r.value) : null
  )

  return {
    kospi: kospiRes,
    nasdaq: nasdaqRes,
    usdkrw: usdkrwRes ? usdkrwRes.value : null,
  }
}

/**
 * 복수 종목 가격 병렬 조회
 */
export async function fetchPrices(
  stocks: { ticker: string; market: string }[]
): Promise<Record<string, PriceData>> {
  const results = await Promise.allSettled(
    stocks.map(s => fetchPrice(s.ticker, s.market))
  )

  const map: Record<string, PriceData> = {}
  results.forEach((r, i) => {
    if (r.status === 'fulfilled' && r.value) {
      map[stocks[i].ticker] = r.value
    }
  })
  return map
}
