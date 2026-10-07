// The one Supabase client the whole app shares. The publishable key is meant for browsers:
// what each user may read or change is enforced by the database's access rules, not by hiding it.
import { createClient } from '@supabase/supabase-js'
import { env } from './env.ts'

export const supabase = createClient(env.supabaseUrl, env.supabasePublishableKey, {
  // Sign-in returns a one-time code that is swapped for a session, rather than putting
  // the session's tokens in the address bar, where browser history would keep them
  auth: { flowType: 'pkce' },
})
