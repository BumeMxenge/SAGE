// Types for the VITE_ settings in frontend/.env, so a misspelt name fails the type check
interface ViteTypeOptions {
  strictImportMetaEnv: unknown // only the names below are allowed
}

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_SUPABASE_URL?: string
  readonly VITE_SUPABASE_PUBLISHABLE_KEY?: string
}
