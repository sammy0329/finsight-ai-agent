import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import SettingsClient from './SettingsClient'
import { type Segment } from '@/types'

export default async function SettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles').select('segment').eq('user_id', user.id).single()
  if (!profile) redirect('/onboarding')

  const { data: watchlist } = await supabase
    .from('watchlist').select('ticker').eq('user_id', user.id)

  return (
    <SettingsClient
      email={user.email ?? ''}
      segment={profile.segment as Segment}
      watchlistCount={watchlist?.length ?? 0}
    />
  )
}
