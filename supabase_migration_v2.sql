ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS tour_completed boolean NOT NULL DEFAULT false;
