'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { type Segment, SEGMENT_LABEL, SEGMENT_ICON } from '@/types'

const SEGMENT_COLOR: Record<Segment, string> = { A: '#3b82f6', B: '#ef4444', C: '#22c55e' }
const SEGMENT_DESC: Record<Segment, string> = {
  A: '안전추구형',
  B: '위험감수형',
  C: '가치투자형',
}

interface Props {
  email: string
  segment: Segment
  watchlistCount: number
}

export default function SettingsClient({ email, segment: initialSegment, watchlistCount }: Props) {
  const router = useRouter()
  const supabase = createClient()
  const [segment, setSegment] = useState<Segment>(initialSegment)
  const [saving, setSaving] = useState(false)

  const color = SEGMENT_COLOR[segment]
  const initial = email.charAt(0).toUpperCase()

  async function changeSegment(seg: Segment) {
    if (seg === segment) return
    setSaving(true)
    const { data: { user } } = await supabase.auth.getUser()
    if (user) {
      await supabase.from('profiles').update({ segment: seg }).eq('user_id', user.id)
    }
    setSegment(seg)
    setSaving(false)
  }

  async function logout() {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <div style={{ color: '#f1f1f1' }}>
      <div className="px-5 pt-5 pb-3">
        <h1 className="text-xl font-bold">설정</h1>
      </div>

      {/* 프로필 카드 */}
      <div className="mx-4 mb-5 p-4 rounded-2xl flex items-center gap-3.5"
        style={{ background: '#1e1e1e' }}>
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-bold text-white"
          style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
          {initial}
        </div>
        <div>
          <p className="font-semibold text-sm">{email.split('@')[0]}</p>
          <p className="text-xs mt-0.5" style={{ color: '#555' }}>{email}</p>
        </div>
      </div>

      {/* 투자 성향 변경 */}
      <div className="mx-4 mb-4 p-4 rounded-2xl" style={{ background: '#1e1e1e' }}>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">투자 성향</h2>
          <span className="text-xs px-2 py-0.5 rounded-full font-bold"
            style={{ background: `${color}26`, color, border: `1px solid ${color}4d` }}>
            {SEGMENT_ICON[segment]} {segment}형 {SEGMENT_LABEL[segment]}
          </span>
        </div>
        <div className="flex gap-2">
          {(['A', 'B', 'C'] as Segment[]).map(seg => (
            <button key={seg} onClick={() => changeSegment(seg)}
              disabled={saving}
              className="flex-1 py-2.5 rounded-xl text-center"
              style={segment === seg
                ? { border: `1px solid ${SEGMENT_COLOR[seg]}`, background: `${SEGMENT_COLOR[seg]}1a` }
                : { border: '1px solid #2a2a2a', background: '#1a1a1a' }
              }>
              <p className="text-xs font-semibold" style={{ color: segment === seg ? SEGMENT_COLOR[seg] : '#888' }}>
                {SEGMENT_ICON[seg]} {seg}형
              </p>
              <p className="text-[10px] mt-0.5" style={{ color: '#555' }}>{SEGMENT_DESC[seg]}</p>
            </button>
          ))}
        </div>
      </div>

      {/* 관심 종목 */}
      <div className="mx-4 mb-2">
        <p className="text-[11px] uppercase tracking-wider mb-2 px-1" style={{ color: '#555' }}>관심 종목 관리</p>
        <div className="rounded-2xl overflow-hidden" style={{ background: '#1e1e1e' }}>
          <button onClick={() => router.push('/search')}
            className="w-full flex items-center justify-between px-4 py-3.5 text-sm">
            <span>등록 종목</span>
            <span style={{ color: '#555' }}>{watchlistCount}개 ›</span>
          </button>
        </div>
      </div>

      {/* 계정 */}
      <div className="mx-4 mb-2 mt-4">
        <p className="text-[11px] uppercase tracking-wider mb-2 px-1" style={{ color: '#555' }}>계정</p>
        <div className="rounded-2xl overflow-hidden" style={{ background: '#1e1e1e' }}>
          <button className="w-full flex items-center justify-between px-4 py-3.5 text-sm">
            <span>비밀번호 변경</span>
            <span style={{ color: '#555' }}>›</span>
          </button>
        </div>
      </div>

      <button onClick={logout}
        className="mx-4 mt-4 w-[calc(100%-32px)] py-3.5 rounded-2xl text-sm font-medium"
        style={{ border: '1px solid #2a2a2a', color: '#f87171', background: 'transparent' }}>
        로그아웃
      </button>

      <p className="text-center text-[11px] mt-4 mb-4" style={{ color: '#333' }}>
        FinSight Agent v0.1.0
      </p>
    </div>
  )
}
