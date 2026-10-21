// Sign-in state for any component: who is signed in and their name, plus sign-in and sign-out
// actions
import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { queryClient } from '@/lib/queryClient.ts'
import { supabase } from '@/lib/supabase.ts'
import { forgetName, lookUpName, type Name } from './name.ts'
import { signInFinished } from './session.ts'

export function useAuth() {
  const [session, setSession] = useState<Session | null>(null)
  const [name, setName] = useState<Name>() // none for Mbali's link, which brings no Microsoft token
  // Until both the sign-in and the name are known, so a greeting never changes once it shows
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // A refused sign-in shows its reason. Every sign-in comes back to /, which always redirects, so the
    // redirect clears the refusal Microsoft or Supabase put in the address bar, or a link's token.
    void signInFinished.then(({ error }) => {
      if (error) setError(error.message)
    })
    let accountId: string | undefined
    // Runs once with the current session, then on every sign-in, sign-out and token refresh
    const { data } = supabase.auth.onAuthStateChange((event, newSession) => {
      if (event === 'SIGNED_OUT' && accountId) forgetName(accountId)
      accountId = newSession?.user.id
      setSession(newSession)
      if (!newSession) {
        setName(undefined)
        setLoading(false)
        return
      }
      // Usually answered already, as the sign-in started the lookup. Microsoft's token rides on the
      // session only until its first refresh, so an event that still carries it can start one too.
      const id = newSession.user.id
      void lookUpName(id, newSession.provider_token).then((found) => {
        // Used only if the same account is still signed in when the name arrives
        if (accountId !== id) return
        setName(found)
        setLoading(false)
      })
    })
    return () => data.subscription.unsubscribe()
  }, [])

  // chooseAccount makes Microsoft show its account picker rather than reuse the account it
  // remembers, for the wrong-account page's Use a Different Account
  async function signIn({ chooseAccount = false } = {}) {
    setError(null)
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'azure', // Microsoft, through the Azure provider set up in Supabase
      options: {
        // email for the account, and Graph's basic profile so this browser can read the name.
        // Not profile, which would put every student's name in Supabase.
        scopes: 'email User.Read',
        redirectTo: `${window.location.origin}/`, // come back to this site, local or hosted
        queryParams: chooseAccount ? { prompt: 'select_account' } : undefined,
      },
    })
    if (error) setError(error.message) // on success the browser has already left for Microsoft
  }

  // The caller then goes to /sign-in. Everything read for this account leaves the cache with it, so
  // the next person to sign in on this browser never sees it. It goes whatever Supabase answers: the
  // student has asked to leave, and supabase-js drops the session even when its logout request fails.
  async function signOut() {
    const { error } = await supabase.auth.signOut()
    queryClient.clear()
    if (error) setError(error.message)
  }

  return { session, name, loading, error, signIn, signOut }
}
