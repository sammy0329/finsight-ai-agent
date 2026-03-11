'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Segment, SEGMENT_LABEL, SEGMENT_ICON } from '@/types'

const SEGMENT_DESC: Record<Segment, string> = {
  A: '리스크를 최소화하며 안정적인 수익을 추구합니다. 배당주, 국채 중심의 보수적 분석을 제공합니다.',
  B: '높은 수익을 위해 변동성을 감수합니다. 성장주, 모멘텀 중심의 공격적 분석을 제공합니다.',
  C: '기업의 내재가치를 분석해 장기 투자합니다. PER, PBR 등 펀더멘털 중심의 분석을 제공합니다.',
}

const SEGMENT_KEYWORDS: Record<Segment, string[]> = {
  A: ['배당주', '국채', '리스크 관리', '분산투자'],
  B: ['성장주', '모멘텀', '해외주식', '테마투자'],
  C: ['PER/PBR', '실적', '장기투자', '내재가치'],
}

const SEGMENT_BORDER: Record<Segment, string> = {
  A: '#3b82f6',
  B: '#ef4444',
  C: '#22c55e',
}


export default function OnboardingPage() {
  const router = useRouter()
  const supabase = createClient()
  const [selected, setSelected] = useState<Segment | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleNext() {
    if (!selected) return
    setLoading(true)
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { router.push('/login'); return }

    await supabase.from('profiles').upsert({
      user_id: user.id,
      segment: selected,
    })
    router.push('/')
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#141414', color: '#f1f1f1' }}>
      <div className="px-6 pt-8 pb-4">
        {/* 스텝 인디케이터 */}
        <div className="flex gap-1.5 mb-6">
          <div className="h-0.5 flex-1 rounded" style={{ background: '#3b82f6' }} />
          <div className="h-0.5 flex-1 rounded" style={{ background: '#2a2a2a' }} />
        </div>
        <h2 className="text-2xl font-bold leading-snug">투자 성향을<br/>선택해주세요</h2>
        <p className="text-sm mt-2" style={{ color: '#666' }}>선택한 성향에 맞는 관점으로 인사이트를 제공합니다</p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-6 flex flex-col gap-3">
        {(['A', 'B', 'C'] as Segment[]).map(seg => (
          <button
            key={seg}
            onClick={() => setSelected(seg)}
            className="w-full text-left p-4 rounded-2xl transition-all"
            style={{
              background: selected === seg ? `${SEGMENT_BORDER[seg]}14` : '#1e1e1e',
              border: `2px solid ${selected === seg ? SEGMENT_BORDER[seg] : 'transparent'}`,
            }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <span className="text-2xl">{SEGMENT_ICON[seg]}</span>
              <span className="font-semibold text-sm">{SEGMENT_LABEL[seg]}</span>
              <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full"
                style={{
                  background: `${SEGMENT_BORDER[seg]}26`,
                  color: SEGMENT_BORDER[seg],
                  border: `1px solid ${SEGMENT_BORDER[seg]}4d`,
                }}>
                {seg}형
              </span>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: '#666' }}>{SEGMENT_DESC[seg]}</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {SEGMENT_KEYWORDS[seg].map(kw => (
                <span key={kw} className="text-xs px-2 py-0.5 rounded-lg" style={{ background: '#2a2a2a', color: '#888' }}>
                  {kw}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      <div className="px-5 pb-8">
        <button
          onClick={handleNext}
          disabled={!selected || loading}
          className="w-full py-3.5 rounded-xl font-semibold text-sm text-white disabled:opacity-40"
          style={{ background: '#3b82f6' }}
        >
          {loading ? '저장 중...' : '다음 — 관심 종목 설정'}
        </button>
      </div>
    </div>
  )
}
