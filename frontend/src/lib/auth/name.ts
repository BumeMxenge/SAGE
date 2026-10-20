// A student's name, read from Microsoft Graph at sign-in and kept only in this browser. SAGE's
// servers never see it: Supabase Auth keeps just the email, which is the account.

export type Name = { givenName: string; surname: string }

// One entry per account, so a shared browser never shows one student another's name
const key = (accountId: string) => `sage-name-${accountId}`

// Each account's lookup on this page, so however many screens ask, and React's second subscription in
// development, Graph is asked once
const lookups = new Map<string, Promise<Name | undefined>>()

export function storedName(accountId: string): Name | undefined {
  try {
    const stored = localStorage.getItem(key(accountId))
    return stored ? (JSON.parse(stored) as Name) : undefined
  } catch {
    return undefined // storage is blocked, as in some private windows, or the entry is unreadable
  }
}

export function keepName(accountId: string, name: Name): void {
  try {
    localStorage.setItem(key(accountId), JSON.stringify(name))
  } catch {
    // storage is blocked, so the name lasts only until the page closes
  }
}

export function forgetName(accountId: string): void {
  lookups.delete(accountId)
  try {
    localStorage.removeItem(key(accountId))
  } catch {
    // storage is blocked, so nothing was kept
  }
}

// How long Graph has to answer, in milliseconds, before a screen goes on without the name
const graphLimit = 3000

// Asks Graph with the Microsoft token the sign-in brought. Any failure, or no answer in time, gives no
// name, on purpose: screens show the student number instead, and a sign-in never fails over a name.
async function nameFromGraph(microsoftToken: string): Promise<Name | undefined> {
  try {
    const response = await fetch('https://graph.microsoft.com/v1.0/me?$select=givenName,surname', {
      headers: { Authorization: `Bearer ${microsoftToken}` },
      signal: AbortSignal.timeout(graphLimit),
    })
    if (!response.ok) return undefined
    const { givenName, surname } = (await response.json()) as Partial<Name>
    return givenName && surname ? { givenName, surname } : undefined
  } catch {
    return undefined
  }
}

// The account's name: the one this browser keeps, or Graph's. The sign-in starts the lookup as soon as
// it finishes, so a screen that asks later usually finds the answer waiting.
export function lookUpName(accountId: string, microsoftToken: string | null | undefined): Promise<Name | undefined> {
  const stored = storedName(accountId)
  if (stored) return Promise.resolve(stored)
  const asked = lookups.get(accountId)
  if (asked) return asked
  // Mbali's link brings no Microsoft token, so she has no name
  if (!microsoftToken) return Promise.resolve(undefined)
  const lookup: Promise<Name | undefined> = nameFromGraph(microsoftToken).then((name) => {
    // A sign-out while Graph was answering forgot the lookup, so its answer isn't kept
    if (name && lookups.get(accountId) === lookup) keepName(accountId, name)
    return name
  })
  lookups.set(accountId, lookup)
  return lookup
}
