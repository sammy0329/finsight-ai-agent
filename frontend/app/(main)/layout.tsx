import BottomNav from '@/components/BottomNav'

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen max-w-md mx-auto" style={{ background: '#141414' }}>
      <main className="flex-1 overflow-y-auto scrollbar-hide pb-20">
        {children}
      </main>
      <BottomNav />
    </div>
  )
}
