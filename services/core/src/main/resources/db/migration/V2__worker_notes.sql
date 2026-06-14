-- Dev notes: workers are created via seller-bot /add_worker (MTProto login).
-- SESSION_ENCRYPTION_KEY must be set (openssl rand -base64 32) in worker-engine and .env.
-- For E2E without MTProto use DEV_INJECT_MESSAGE + manual seller/product from /start.
SELECT 1;
