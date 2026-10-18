// A student's name, read from Microsoft Graph at sign-in and kept only in this browser. SAGE's
// servers never see it: Supabase Auth keeps just the email, which is the account.

export type Name = { givenName: string; surname: string }

// One entry per account, so a shared browser never shows one student another's name
const key = (accountId: string) => `sage-name-${accountId}`

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
  try {
    localStorage.removeItem(key(accountId))
  } catch {
    // storage is blocked, so nothing was kept
  }
}

// Asks Graph once, with the Microsoft token the sign-in brought. Any failure gives no name, on
// purpose: screens show the student number instead, and a sign-in never fails over a name.
export async function nameFromGraph(microsoftToken: string): Promise<Name | undefined> {
  try {
    const response = await fetch('https://graph.microsoft.com/v1.0/me?$select=givenName,surname', {
      headers: { Authorization: `Bearer ${microsoftToken}` },
    })
    if (!response.ok) return undefined
    const { givenName, surname } = (await response.json()) as Partial<Name>
    return givenName && surname ? { givenName, surname } : undefined
  } catch {
    return undefined
  }
}
