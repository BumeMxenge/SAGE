// Calls to the SAGE backend (FastAPI). Every request goes through here, so the address lives in one place.
import { env } from './env.ts'

export type Health = { status: string; commit: string }

export async function getHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch(`${env.apiUrl}/health`, { signal })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return (await response.json()) as Health
}
