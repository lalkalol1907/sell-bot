ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_notifications_pending_created
    ON notifications (created_at)
    WHERE delivery_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_notifications_processing_claimed
    ON notifications (claimed_at)
    WHERE delivery_status = 'processing';
