-- Spam phrases learned from seller feedback
CREATE TABLE spam_phrases (
    id              BIGSERIAL PRIMARY KEY,
    seller_id       BIGINT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    phrase          TEXT NOT NULL,
    source_lead_id  BIGINT REFERENCES leads(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (seller_id, phrase)
);

CREATE INDEX idx_spam_phrases_seller_id ON spam_phrases(seller_id);

-- Outbox: notifications can be pending until published to NATS
ALTER TABLE notifications
    ALTER COLUMN sent_at DROP NOT NULL,
    ALTER COLUMN sent_at DROP DEFAULT,
    ALTER COLUMN delivery_status SET DEFAULT 'pending';

ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS attempts INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
