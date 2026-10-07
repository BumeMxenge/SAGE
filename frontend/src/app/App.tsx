// The M0 shell. It proves two things: the browser can reach the backend (VITE_API_URL and CORS),
// and a student can sign in with their UCT Microsoft account through Supabase.
import { useEffect, useState } from 'react'
import { useAuth } from '../features/auth/useAuth.ts'
import { getHealth, type Health } from '../lib/api.ts'
import { env } from '../lib/env.ts'

type Backend = { state: 'checking' } | { state: 'up'; health: Health } | { state: 'down' }

// One plain sentence for each state of the backend check
function describe(backend: Backend): string {
  switch (backend.state) {
    case 'checking':
      return 'Checking the backend…'
    case 'up': {
      const { commit } = backend.health // "dev" when the backend runs on your laptop
      return `Backend is up, running ${commit === 'dev' ? 'a local build' : `commit ${commit.slice(0, 7)}`}.`
    }
    case 'down':
      return `Can't reach the backend at ${env.apiUrl}. Check it's running and that it allows this site (CORS).`
  }
}

function App() {
  const auth = useAuth()
  const [backend, setBackend] = useState<Backend>({ state: 'checking' })

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then((health) => setBackend({ state: 'up', health }))
      .catch(() => {
        if (!controller.signal.aborted) setBackend({ state: 'down' })
      })
    // In development React runs this twice on purpose; cancelling stops the first request racing the second
    return () => controller.abort()
  }, [])

  return (
    <main className="shell">
      <header className="brand">
        <img src="/sage-symbol.svg" alt="" width="40" height="48" />
        <div>
          <h1>SAGE</h1>
          <p>Student Advisor for Guided Enrolment</p>
        </div>
      </header>

      <section className="account">
        {auth.loading ? (
          <p>Checking your sign-in…</p>
        ) : auth.session ? (
          <>
            <p>
              Signed in as <strong>{auth.session.user.email}</strong>
            </p>
            <button type="button" className="secondary" onClick={() => void auth.signOut()}>
              Sign out
            </button>
          </>
        ) : (
          <button type="button" onClick={() => void auth.signIn()}>
            Continue with UCT email
          </button>
        )}
        {auth.error && (
          <p className="error" role="alert">
            Sign-in failed: {auth.error}
          </p>
        )}
      </section>

      <p className={`status ${backend.state}`} role="status">
        {describe(backend)}
      </p>
    </main>
  )
}

export default App
