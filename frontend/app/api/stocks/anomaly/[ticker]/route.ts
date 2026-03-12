import { NextRequest } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL!
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY!

export async function GET(
  _: NextRequest,
  { params }: { params: { ticker: string } }
) {
  try {
    const res = await fetch(
      `${FASTAPI_URL}/api/ai/anomaly/${params.ticker}`,
      {
        headers: { 'X-Internal-Key': INTERNAL_API_KEY },
        next: { revalidate: 1800 },
      }
    )
    if (!res.ok) throw new Error('FastAPI error')
    return Response.json(await res.json())
  } catch {
    return Response.json({ ticker: params.ticker, is_anomaly: false, zscore: null, message: '조회 실패' })
  }
}
