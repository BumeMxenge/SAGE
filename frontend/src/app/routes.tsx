// The browser's addresses: one route for each page, saying who may open it and where its page lives.
// A page loads only when first opened, from a fixed file in the folder of the branch that builds it,
// so a later branch replaces that file and never edits this table. The table lives in app/, as lib/
// may not import a feature.
import type { ComponentType } from 'react'
import { replace, type RouteObject } from 'react-router'
import { ApiError } from '@/lib/api.ts'
import { signInFinished } from '@/lib/auth/session.ts'
import { pageNames, pageTitle } from '@/lib/copy.ts'
import { queryClient } from '@/lib/queryClient.ts'
import { queries } from '@/lib/queryKeys.ts'
import { supabase } from '@/lib/supabase.ts'
import { Root } from './Root.tsx'
import { RouteError } from './RouteError.tsx'

// Who is visiting, as far as SAGE is concerned
type Visitor = 'signed_out' | 'refused' | 'staff' | 'onboarding' | 'student'

// Where each visitor belongs, and goes from any page they may not open
const home: Record<Visitor, string> = {
  signed_out: '/sign-in',
  refused: '/wrong-account',
  staff: '/staff',
  onboarding: '/onboarding',
  student: '/plan',
}

async function visitor(): Promise<Visitor> {
  // A sign-in still finishing in the address bar ends first, or it would be sent away half done
  await signInFinished
  const { data } = await supabase.auth.getSession()
  if (!data.session) return 'signed_out'
  try {
    // From the cache once asked, until Finish Setup refreshes it
    const me = await queryClient.query(queries.me())
    if (me.account === 'staff') return 'staff'
    return me.onboarding_complete ? 'student' : 'onboarding'
  } catch (error) {
    // The API refused the session, or the account isn't a UCT one. Anything else, such as SAGE not
    // answering, shows the route error page.
    if (error instanceof ApiError && error.code === 'not_signed_in') return 'signed_out'
    if (error instanceof ApiError && error.code === 'uct_account_required') return 'refused'
    throw error
  }
}

// The loader of a page that one kind of visitor may open. Everyone else goes home, replacing the
// address, so Back never returns to a page that sends them away, and a sign-in link's token leaves
// no entry in the browser's history.
const guard = (opens: Visitor) => async () => {
  const who = await visitor()
  if (who !== opens) throw replace(home[who])
  return null
}

type Page = { path: string; opens: Visitor; name: string; load: () => Promise<{ Component: ComponentType }> }

const page = ({ path, opens, name, load }: Page): RouteObject => ({
  path,
  loader: guard(opens),
  handle: { title: pageTitle(name) },
  lazy: load,
})

export const routes: RouteObject[] = [
  {
    Component: Root,
    ErrorBoundary: RouteError,
    // Nothing shows until the guard has decided, so no page flashes before a redirect
    HydrateFallback: () => null,
    children: [
      // / keeps no one: it sends each visitor home
      {
        index: true,
        loader: async () => {
          throw replace(home[await visitor()])
        },
      },
      page({
        path: '/sign-in',
        opens: 'signed_out',
        name: pageNames.signIn,
        load: async () => ({ Component: (await import('@/features/onboarding/SignInPage.tsx')).SignInPage }),
      }),
      page({
        path: '/onboarding',
        opens: 'onboarding',
        name: pageNames.onboarding,
        load: async () => ({ Component: (await import('@/features/onboarding/OnboardingPage.tsx')).OnboardingPage }),
      }),
      page({
        path: '/wrong-account',
        opens: 'refused',
        name: pageNames.wrongAccount,
        load: async () => ({ Component: (await import('@/features/onboarding/WrongAccountPage.tsx')).WrongAccountPage }),
      }),
      page({
        path: '/staff',
        opens: 'staff',
        name: pageNames.staff,
        load: async () => ({ Component: (await import('./StaffPage.tsx')).StaffPage }),
      }),
      {
        // The student's pages, in the shell's frame
        lazy: async () => ({ Component: (await import('./AppLayout.tsx')).AppLayout }),
        children: [
          page({
            path: '/plan',
            opens: 'student',
            name: pageNames.plan,
            load: async () => ({ Component: (await import('./PlanWorkspace.tsx')).PlanWorkspace }),
          }),
          page({
            path: '/plan/:planId',
            opens: 'student',
            name: pageNames.plan,
            load: async () => ({ Component: (await import('./PlanWorkspace.tsx')).PlanWorkspace }),
          }),
          page({
            path: '/electives',
            opens: 'student',
            name: pageNames.electives,
            load: async () => ({ Component: (await import('@/features/electives/ElectivesPage.tsx')).ElectivesPage }),
          }),
          page({
            path: '/history',
            opens: 'student',
            name: pageNames.history,
            load: async () => ({ Component: (await import('@/features/history/HistoryPage.tsx')).HistoryPage }),
          }),
          // An address that isn't a page. It sits in the student's frame, so only a student sees it;
          // anyone else goes home.
          page({
            path: '*',
            opens: 'student',
            name: pageNames.notFound,
            load: async () => ({ Component: (await import('./NotFoundPage.tsx')).NotFoundPage }),
          }),
        ],
      },
    ],
  },
]
