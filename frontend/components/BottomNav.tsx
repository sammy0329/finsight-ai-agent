'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  {
    href: '/',
    label: '홈',
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
        <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"
          stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinejoin="round"/>
      </svg>
    ),
  },
  {
    href: '/search',
    label: '검색',
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
        <circle cx="11" cy="11" r="7" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8"/>
        <path d="M20 20l-3-3" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    href: '/history',
    label: '이력',
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
        <rect x="4" y="4" width="16" height="16" rx="2" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8"/>
        <path d="M8 9h8M8 13h5" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    ),
  },
  {
    href: '/settings',
    label: '설정',
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
        <circle cx="12" cy="8" r="3" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8"/>
        <path d="M5 20c0-3.87 3.13-7 7-7s7 3.13 7 7" stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    ),
  },
]

export default function BottomNav() {
  const pathname = usePathname()

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 max-w-md mx-auto flex justify-around py-2.5 pb-safe"
      style={{ background: '#1a1a1a', borderTop: '1px solid #252525' }}
    >
      {navItems.map(item => {
        const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
        return (
          <Link
            key={item.href}
            href={item.href}
            className="flex flex-col items-center gap-1"
            style={{ opacity: active ? 1 : 0.45 }}
          >
            {item.icon(active)}
            <span className="text-[10px]" style={{ color: '#f1f1f1' }}>{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
