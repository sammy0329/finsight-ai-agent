import BottomNav from '@/components/BottomNav'
import { createClient } from '@/lib/supabase/server'

async function getUnreadCount(): Promise<number> {
  try {
    const supabase = await createClient()
    const {
      data: { user },
    } = await supabase.auth.getUser()
    if (!user) return 0
    const { count } = await supabase
      .from('notifications')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .eq('is_read', false)
    return count ?? 0
  } catch {
    return 0
  }
}

export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const unreadCount = await getUnreadCount()

  return (
    <div className="flex flex-col min-h-screen max-w-md mx-auto" style={{ background: '#141414' }}>
      <main className="flex-1 overflow-y-auto scrollbar-hide pb-20">{children}</main>
      <BottomNav reportsUnread={unreadCount} />
    </div>
  )
}
