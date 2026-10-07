// Sign-in state for any component: who is signed in, plus sign-in and sign-out actions
import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase.ts'

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Supabase finishes a sign-in that has just come back from Microsoft as it starts up.
    // If Microsoft or Supabase refused it, the reason is in the address bar; show it once.
    void supabase.auth.initialize().then(({ error }) => {
      if (error) {
        setError(error.message)
        window.history.replaceState(null, '', window.location.pathname)
      }
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
