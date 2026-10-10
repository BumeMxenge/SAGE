-- Supabase's optional "Enable automatic RLS" setting installs these on the hosted project only.
-- Our migrations enable RLS on every table themselves and CI checks it, so they are redundant.
-- "if exists" makes this a no-op locally.
drop event trigger if exists ensure_rls;
drop function if exists public.rls_auto_enable();
