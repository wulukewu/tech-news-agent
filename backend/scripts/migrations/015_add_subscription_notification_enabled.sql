-- Migration 015: Add notification_enabled to user_subscriptions
-- Allows per-feed notification control

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS notification_enabled BOOLEAN NOT NULL DEFAULT true;

COMMENT ON COLUMN user_subscriptions.notification_enabled IS 'Whether the user wants DM notifications for articles from this feed';
