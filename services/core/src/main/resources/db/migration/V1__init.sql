-- sellers
CREATE TABLE sellers (
    id              BIGSERIAL PRIMARY KEY,
    tg_user_id      BIGINT NOT NULL UNIQUE,
    username        TEXT,
    full_name       TEXT,
    plan            TEXT NOT NULL DEFAULT 'free',
    sensitivity     TEXT NOT NULL DEFAULT 'precise',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- products
CREATE TABLE products (
    id              BIGSERIAL PRIMARY KEY,
    seller_id       BIGINT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    price           NUMERIC(12, 2) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    keywords        TEXT[] NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_seller_id ON products(seller_id);

-- workers
CREATE TABLE workers (
    id              BIGSERIAL PRIMARY KEY,
    owner_seller_id BIGINT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    tg_account_id   BIGINT,
    phone           TEXT,
    session_enc     BYTEA,
    proxy           TEXT,
    status          TEXT NOT NULL DEFAULT 'paused',
    last_seen_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workers_owner_seller_id ON workers(owner_seller_id);
CREATE INDEX idx_workers_status ON workers(status);

-- monitored_chats
CREATE TABLE monitored_chats (
    id              BIGSERIAL PRIMARY KEY,
    worker_id       BIGINT NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    chat_id         BIGINT NOT NULL,
    title           TEXT,
    type            TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (worker_id, chat_id)
);

CREATE INDEX idx_monitored_chats_worker_id ON monitored_chats(worker_id);

-- leads
CREATE TABLE leads (
    id                  BIGSERIAL PRIMARY KEY,
    seller_id           BIGINT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    product_id          BIGINT REFERENCES products(id) ON DELETE SET NULL,
    worker_id           BIGINT REFERENCES workers(id) ON DELETE SET NULL,
    chat_id             BIGINT NOT NULL,
    message_id          BIGINT NOT NULL,
    author_id           BIGINT NOT NULL,
    author_username     TEXT,
    raw_text            TEXT NOT NULL,
    matched_keywords    TEXT[] NOT NULL DEFAULT '{}',
    product_score       NUMERIC(5, 4) NOT NULL DEFAULT 0,
    intent_score        NUMERIC(5, 4) NOT NULL DEFAULT 0,
    score               NUMERIC(5, 4) NOT NULL DEFAULT 0,
    level               TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'new',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leads_seller_status_created ON leads(seller_id, status, created_at DESC);

-- notifications
CREATE TABLE notifications (
    id              BIGSERIAL PRIMARY KEY,
    lead_id         BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    seller_id       BIGINT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
    sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivery_status TEXT NOT NULL DEFAULT 'sent'
);
