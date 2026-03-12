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
    href: '/reports',
    label: '리포트',
    icon: (active: boolean) => (
      <svg viewBox="0 0 24 24" fill="none" width="22" height="22">
        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"
          stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M13.73 21a2 2 0 01-3.46 0"
          stroke={active ? '#f1f1f1' : '#555'} strokeWidth="1.8" strokeLinecap="round"/>
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

interface BottomNavProps {
  reportsUnread?: number
}

export default function BottomNav({ reportsUnread = 0 }: BottomNavProps) {
  const pathname = usePathname()

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 max-w-md mx-auto flex justify-around py-2.5 pb-safe"
      style={{ background: '#1a1a1a', borderTop: '1px solid #252525' }}
    >
      {navItems.map(item => {
        const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
        const isReports = item.href === '/reports'
        return (
          <Link
            key={item.href}
            href={item.href}
            className="flex flex-col items-center gap-1"
            style={{ opacity: active ? 1 : 0.45 }}
          >
            <span className="relative">
              {item.icon(active)}
              {isReports && reportsUnread > 0 && (
                <span
                  className="absolute -top-1 -right-1 flex items-center justify-center text-[9px] font-bold rounded-full"
                  style={{
                    background: '#ef4444',
                    color: '#fff',
                    minWidth: '14px',
                    height: '14px',
                    padding: '0 3px',
                  }}
                >
                  {reportsUnread > 99 ? '99+' : reportsUnread}
                </span>
              )}
            </span>
            <span className="text-[10px]" style={{ color: '#f1f1f1' }}>{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
