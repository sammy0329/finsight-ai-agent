import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  _: NextRequest,
  { params }: { params: Promise<{ ticker: string }> }
) {
  const { ticker } = await params
  const supabase = await createClient()

  const { data, error } = await supabase
    .from('financial_metrics')
    .select('*')
    .eq('ticker', ticker)
    .order('period', { ascending: false })
    .limit(1)
    .single()

  if (error || !data) {
    return NextResponse.json(null)
  }

  return NextResponse.json(data, {
    headers: { 'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400' },
  })
}
