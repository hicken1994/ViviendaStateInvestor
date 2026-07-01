-- =============================================
-- Migration v4: Stripe fields + idealista cache flag
-- Run this in Supabase SQL Editor
-- =============================================

ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS stripe_customer_id text;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS stripe_subscription_id text;
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS subscription_status text NOT NULL DEFAULT 'inactive';

CREATE TABLE IF NOT EXISTS idealista_search_cache (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    search_params jsonb NOT NULL,
    results_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE idealista_search_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own search cache"
    ON idealista_search_cache FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own search cache"
    ON idealista_search_cache FOR INSERT
    WITH CHECK (auth.uid() = user_id);
