# Build context: services/web (monorepo root)
FROM oven/bun:1.3.14-alpine AS builder
WORKDIR /app

COPY .npmrc package.json bun.lock ./
COPY packages/api-client/package.json packages/api-client/
COPY apps/login-miniapp/package.json apps/login-miniapp/
COPY apps/seller-dashboard/package.json apps/seller-dashboard/
RUN bun install --frozen-lockfile

COPY packages/api-client/ packages/api-client/
COPY apps/login-miniapp/ apps/login-miniapp/
RUN bun run --filter @sellbot/login-miniapp build

FROM nginx:1.27-alpine
COPY apps/login-miniapp/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/login-miniapp/dist /usr/share/nginx/html/miniapp
EXPOSE 80
