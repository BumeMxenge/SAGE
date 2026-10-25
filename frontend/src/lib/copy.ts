// SAGE's shared words: the product name, the navigation, the appearance options, the terms, and each
// page's name and title. Every page has its own title, such as "Course History · SAGE", so the browser
// tab and a screen reader say where the student is (WCAG 2.4.2). The route table sets it.
import type { components } from './api-types.ts'
import type { Appearance } from './useAppearance.ts'

const productName = 'SAGE'

export const nav = { plan: 'Plan', electives: 'Explore Electives', history: 'Course History' }

export const appearanceOptions: Record<Appearance, string> = {
  system: 'Match System',
  light: 'Light',
  dark: 'Dark',
}

// Each term a course runs in, as the prototypes write it. A Record over the API's terms, so a term the
// API adds fails the build until it has words here.
export const termLabels: Record<components['schemas']['CatalogueCourse']['term'], string> = {
  q1: 'Q1',
  q2: 'Q2',
  q3: 'Q3',
  q4: 'Q4',
  sem1: 'Sem 1',
  sem2: 'Sem 2',
  full_year: 'Full year',
  winter: 'Winter',
  summer: 'Summer',
  other: 'Other',
}

// Each page's name, which starts its title, and is its heading while the page is a stub
export const pageNames = {
  signIn: 'Sign In',
  onboarding: 'Set Up Your Account',
  wrongAccount: 'Wrong Account',
  staff: 'Staff Tools',
  plan: nav.plan,
  electives: nav.electives,
  history: nav.history,
  notFound: 'Page Not Found',
}

export const pageTitle = (name: string) => `${name} · ${productName}`
