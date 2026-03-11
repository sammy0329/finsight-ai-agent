'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const router = useRouter()
  const supabase = createClient()

  // 로그인
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  // 회원가입 모달
  const [showSignUp, setShowSignUp] = useState(false)
  const [signUpEmail, setSignUpEmail] = useState('')
  const [signUpPassword, setSignUpPassword] = useState('')
  const [signUpConfirm, setSignUpConfirm] = useState('')
  const [signUpError, setSignUpError] = useState('')
  const [signUpLoading, setSignUpLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoginError('')
    setLoginLoading(true)
    const { error } = await supabase.auth.signInWithPassword({
      email: loginEmail,
      password: loginPassword,
    })
    if (error) { setLoginError(error.message); setLoginLoading(false); return }
    router.push('/')
  }

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault()
    setSignUpError('')
    if (signUpPassword !== signUpConfirm) {
      setSignUpError('비밀번호가 일치하지 않습니다')
      return
    }
    if (signUpPassword.length < 6) {
      setSignUpError('비밀번호는 6자 이상이어야 합니다')
      return
    }
    setSignUpLoading(true)
    const { error } = await supabase.auth.signUp({
      email: signUpEmail,
      password: signUpPassword,
    })
    if (error) { setSignUpError(error.message); setSignUpLoading(false); return }
    router.push('/onboarding')
  }

  function openSignUp() {
    setSignUpEmail('')
    setSignUpPassword('')
    setSignUpConfirm('')
    setSignUpError('')
    setShowSignUp(true)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12"
      style={{ background: '#141414', color: '#f1f1f1' }}>

      <div className="w-full max-w-sm">
        {/* 로고 */}
        <div className="text-center mb-10">
          <div className="w-14 h-14 rounded-2xl mx-auto mb-3 flex items-center justify-center text-2xl"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
            📈
          </div>
          <h1 className="text-2xl font-bold">FinSight</h1>
          <p className="text-sm mt-1" style={{ color: '#555' }}>AI 기반 개인화 투자 인사이트</p>
        </div>

        {/* 로그인 폼 */}
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#888' }}>이메일</label>
            <input
              type="email"
              value={loginEmail}
              onChange={e => setLoginEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full px-3.5 py-3 rounded-xl text-sm outline-none"
              style={{ background: '#1e1e1e', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
            />
          </div>
          <div>
            <label className="block text-xs mb-1.5" style={{ color: '#888' }}>비밀번호</label>
            <input
              type="password"
              value={loginPassword}
              onChange={e => setLoginPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-3.5 py-3 rounded-xl text-sm outline-none"
              style={{ background: '#1e1e1e', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
            />
          </div>

          {loginError && <p className="text-xs" style={{ color: '#f87171' }}>{loginError}</p>}

          <button
            type="submit"
            disabled={loginLoading}
            className="w-full py-3.5 rounded-xl font-semibold text-sm text-white mt-1 disabled:opacity-50"
            style={{ background: '#3b82f6' }}
          >
            {loginLoading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <p className="text-center text-sm mt-5" style={{ color: '#555' }}>
          계정이 없으신가요?{' '}
          <button onClick={openSignUp} className="font-medium" style={{ color: '#3b82f6' }}>
            회원가입
          </button>
        </p>
      </div>

      {/* 회원가입 슬라이드업 모달 */}
      {showSignUp && (
        <>
          {/* 딤 배경 */}
          <div
            className="fixed inset-0 z-40"
            style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
            onClick={() => setShowSignUp(false)}
          />

          {/* 바텀 시트 */}
          <div
            className="fixed bottom-0 left-0 right-0 z-50 rounded-t-3xl px-6 pt-5 pb-10"
            style={{ background: '#1e1e1e', maxWidth: '448px', margin: '0 auto' }}
          >
            {/* 핸들 */}
            <div className="w-10 h-1 rounded-full mx-auto mb-5" style={{ background: '#333' }} />

            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold">회원가입</h2>
              <button
                onClick={() => setShowSignUp(false)}
                className="w-8 h-8 rounded-xl flex items-center justify-center text-sm"
                style={{ background: '#2a2a2a', color: '#888' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSignUp} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs mb-1.5" style={{ color: '#888' }}>이메일</label>
                <input
                  type="email"
                  value={signUpEmail}
                  onChange={e => setSignUpEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoFocus
                  className="w-full px-3.5 py-3 rounded-xl text-sm outline-none"
                  style={{ background: '#141414', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1.5" style={{ color: '#888' }}>비밀번호</label>
                <input
                  type="password"
                  value={signUpPassword}
                  onChange={e => setSignUpPassword(e.target.value)}
                  placeholder="6자 이상"
                  required
                  className="w-full px-3.5 py-3 rounded-xl text-sm outline-none"
                  style={{ background: '#141414', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1.5" style={{ color: '#888' }}>비밀번호 확인</label>
                <input
                  type="password"
                  value={signUpConfirm}
                  onChange={e => setSignUpConfirm(e.target.value)}
                  placeholder="비밀번호 재입력"
                  required
                  className="w-full px-3.5 py-3 rounded-xl text-sm outline-none"
                  style={{ background: '#141414', border: '1px solid #2e2e2e', color: '#f1f1f1' }}
                />
              </div>

              {signUpError && <p className="text-xs" style={{ color: '#f87171' }}>{signUpError}</p>}

              <button
                type="submit"
                disabled={signUpLoading}
                className="w-full py-3.5 rounded-xl font-semibold text-sm text-white mt-1 disabled:opacity-50"
                style={{ background: '#3b82f6' }}
              >
                {signUpLoading ? '처리 중...' : '회원가입 완료'}
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  )
}
