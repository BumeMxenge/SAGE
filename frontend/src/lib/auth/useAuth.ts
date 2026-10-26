// Sign-in state for any component: the name of whoever is signed in, and the sign-in and sign-out
// actions
import { useEffect, useState } from 'react'
import { queryClient } from '@/lib/queryClient.ts'
import { supabase } from '@/lib/supabase.ts'
import { forgetName, lookUpName, type Name } from './name.ts'

export function useAuth() {
  const [name, setName] = useState<Name>() // none for Mbali's link, which brings no Microsoft token
  // Until both the sign-in and the name are known, so a greeting never changes once it shows
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let accountId: string | undefined
    // Runs once with the current session, then on every sign-in, sign-out and token refresh
    const { data } = supabase.auth.onAuthStateChange((event, newSession) => {
      if (event === 'SIGNED_OUT' && accountId) forgetName(accountId)
      accountId = newSession?.user.id
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

  async function signIn() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'azure', // Microsoft, through the Azure provider set up in Supabase
      options: {
        // email for the account, and Graph's basic profile so this browser can read the name.
        // Not profile, which would put every student's name in Supabase.
        scopes: 'email User.Read',
        redirectTo: `${window.location.origin}/`, // come back to this site, local or hosted
      },
    })
    if (error) throw error // on success the browser has already left for Microsoft
  }

  // Signs out of Supabase, leaves the student's pages as the caller says, then empties the cache, so
  // nothing read for this account stays in the page for the next person to sign in on this browser.
  // The cache empties only once her pages have closed, so none of them asks for its reads again,
  // unsigned, on the way out. It empties whatever Supabase answers, and however leaving goes: the
  // student has asked to leave, and supabase-js drops the session even when its logout request fails.
  async function signOut(leave: () => void | Promise<void>) {
    await supabase.auth.signOut()
    try {
      await leave()
    } finally {
      queryClient.clear()
    }
  }

  return { name, loading, signIn, signOut }
}
