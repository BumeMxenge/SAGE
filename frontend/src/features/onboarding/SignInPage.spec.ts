// Parity for the sign-in stub's one control, Continue with UCT Email, against the onboarding
// prototype's Landing state. The onboarding branch replaces the stub and adds its own cases here.
import { parity } from '../../../e2e/parity.ts'

parity('onboarding', [
  {
    name: 'sign-in-button',
    prototype: 'onboarding',
    reach: async (page, theme) => {
      if (theme === 'dark') return null // onboarding has no dark design
      await page.getByRole('button', { name: 'Landing' }).click()
      return page.getByRole('button', { name: 'Continue with UCT email' })
    },
    react: { path: '/sign-in', element: (page) => page.getByRole('button', { name: 'Continue with UCT Email' }) },
    hover: true,
  },
])
