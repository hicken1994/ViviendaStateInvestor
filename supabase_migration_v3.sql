ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS plan text NOT NULL DEFAULT 'Starter';
