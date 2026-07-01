-- =============================================
-- Migration v5: Admin support
-- 1. Add is_admin column to user_preferences
-- 2. RLS policy for admins (bypass for SELECT/UPDATE)
-- =============================================

ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS is_admin boolean NOT NULL DEFAULT false;

-- Admin bypass: admins can read all rows
CREATE POLICY "Admins can view all preferences"
    ON user_preferences FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_preferences
            WHERE user_id = auth.uid() AND is_admin = true
        )
    );

-- Admin bypass: admins can update any row
CREATE POLICY "Admins can update all preferences"
    ON user_preferences FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM user_preferences
            WHERE user_id = auth.uid() AND is_admin = true
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_preferences
            WHERE user_id = auth.uid() AND is_admin = true
        )
    );

-- ⚠️ After running this, mark the admin user:
-- UPDATE user_preferences SET is_admin = true
-- WHERE user_id = (SELECT id FROM auth.users WHERE email = 'julianrincon434@gmail.com');
