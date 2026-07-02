-- Fix infinite recursion in user_preferences RLS policies.
-- Run this in Supabase SQL Editor.
-- Root cause: supabase_migration_v5.sql added admin policies that query
-- user_preferences FROM WITHIN a policy on user_preferences → infinite loop.
-- Fix: drop recursive admin policies; admin check is handled in utils/admin.py.

DROP POLICY IF EXISTS "Admins can view all preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Admins can update all preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can read own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can insert own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can update own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can delete own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Enable read access for users based on user_id" ON public.user_preferences;
DROP POLICY IF EXISTS "Enable insert for users based on user_id" ON public.user_preferences;
DROP POLICY IF EXISTS "Enable update for users based on user_id" ON public.user_preferences;
DROP POLICY IF EXISTS "enable_read_own" ON public.user_preferences;
DROP POLICY IF EXISTS "enable_insert_own" ON public.user_preferences;
DROP POLICY IF EXISTS "enable_update_own" ON public.user_preferences;

-- Create clean non-recursive policies (simple auth.uid() = user_id)
CREATE POLICY "enable_read_own"
ON public.user_preferences FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "enable_insert_own"
ON public.user_preferences FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "enable_update_own"
ON public.user_preferences FOR UPDATE
USING (auth.uid() = user_id);
