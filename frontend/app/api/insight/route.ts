import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { ticker, query, segment } = await request.json()
  if (!ticker || !query || !segment) {
    return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
  }

  const fastApiUrl = process.env.FASTAPI_URL ?? 'http://localhost:8000'
  const internalKey = process.env.INTERNAL_API_KEY ?? ''

  // FastAPI 스트리밍 호출
  const res = await fetch(`${fastApiUrl}/api/ai/insight/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Key': internalKey,
    },
    body: JSON.stringify({
      user_segment: segment,
      query: `${ticker} ${query}`,
    }),
  })

  if (!res.ok) {
    return NextResponse.json({ error: 'FastAPI error' }, { status: 502 })
  }

  // 스트림을 클라이언트로 그대로 전달
  return new NextResponse(res.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
