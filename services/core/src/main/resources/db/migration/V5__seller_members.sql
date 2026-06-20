CREATE TABLE seller_members (
    id          BIGSERIAL PRIMARY KEY,
    seller_id   BIGINT       NOT NULL REFERENCES sellers (id) ON DELETE CASCADE,
    tg_user_id  BIGINT,
    username    VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255),
    status      VARCHAR(32)  NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    joined_at   TIMESTAMPTZ,
    CONSTRAINT uq_seller_members_seller_username UNIQUE (seller_id, username),
    CONSTRAINT uq_seller_members_seller_tg_user UNIQUE (seller_id, tg_user_id)
);

CREATE INDEX idx_seller_members_tg_user_id ON seller_members (tg_user_id) WHERE tg_user_id IS NOT NULL;
CREATE INDEX idx_seller_members_username_lower ON seller_members (LOWER(username));
