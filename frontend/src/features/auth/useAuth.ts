// Sign-in state for any component: who is signed in, plus sign-in and sign-out actions
import type { AuthError, Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { env } from '../../lib/env.ts'
import { supabase } from '../../lib/supabase.ts'

// A link from `make sign-in` carries a one-time token, swapped for a session here once per page
// load, as React runs effects twice in development. Only on local Supabase: on the hosted site,
// such a link could sign a student into someone else's account. Otherwise Supabase starts up as
// usual, finishing a sign-in that has just come back from Microsoft.
const localSupabase = ['127.0.0.1', 'localhost'].includes(new URL(env.supabaseUrl).hostname)
const linkToken = localSupabase ? new URLSearchParams(window.location.search).get('token_hash') : null
const started: Promise<{ error: AuthError | null }> = linkToken
  ? supabase.auth.verifyOtp({ token_hash: linkToken, type: 'magiclink' })
  : supabase.auth.initialize()

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // A refused sign-in shows its reason once. The address bar loses the refusal Microsoft or
    // Supabase put there, or a link's token, which is spent either way.
    void started.then(({ error }) => {
      if (error) setError(error.message)
      if (error || linkToken) window.history.replaceState(null, '', window.location.pathname)
    })
    // Runs once with the current session, then on every sign-in, sign-out and token refresh
    const { data } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
      setLoading(false)
    })
    return () => data.subscription.unsubscribe()
  }, [])

  async function signIn() {
    setError(null)
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'azure', // Microsoft, through the Azure provider set up in Supabase
      options: {
        scopes: 'email', // without it Microsoft doesn't share the email address
        redirectTo: `${window.location.origin}/`, // come back to this site, local or hosted
      },
    })
    if (error) setError(error.message) // on success the browser has already left for Microsoft
  }

  async function signOut() {
    const { error } = await supabase.auth.signOut()
    if (error) setError(error.message)
  }

  return { session, loading, error, signIn, signOut }
}
