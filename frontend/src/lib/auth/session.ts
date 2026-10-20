// The sign-in waiting in the address bar when the page loads, finished once per page load. The guard
// waits for it before it decides where a visitor belongs, so it never sends a sign-in away half done.
// A link from `make sign-in` carries a one-time token, swapped for a session here. Only on local
// Supabase: on the hosted site, such a link could sign a student into someone else's account.
// Otherwise Supabase starts up as usual, finishing a sign-in that has just come back from Microsoft.
import type { AuthError } from '@supabase/supabase-js'
import { env } from '@/lib/env.ts'
import { supabase } from '@/lib/supabase.ts'
import { lookUpName } from './name.ts'

const localSupabase = ['127.0.0.1', 'localhost'].includes(new URL(env.supabaseUrl).hostname)
const linkToken = localSupabase ? new URLSearchParams(window.location.search).get('token_hash') : null

export const signInFinished: Promise<{ error: AuthError | null }> = linkToken
  ? supabase.auth.verifyOtp({ token_hash: linkToken, type: 'magiclink' })
  : supabase.auth.initialize()

// The name's lookup starts as soon as the sign-in finishes, alongside the guard's own reads, so the
// first screen to greet the student usually finds the name waiting
void signInFinished.then(async () => {
  const { data } = await supabase.auth.getSession()
  if (data.session) void lookUpName(data.session.user.id, data.session.provider_token)
})
