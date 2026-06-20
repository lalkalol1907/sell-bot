# Build context: services/web (monorepo root)
FROM oven/bun:1.3.14-alpine AS builder
WORKDIR /app

ARG VITE_BOT_USERNAME=
ARG VITE_MINIAPP_URL=/miniapp/
ENV VITE_BOT_USERNAME=$VITE_BOT_USERNAME
ENV VITE_MINIAPP_URL=$VITE_MINIAPP_URL

COPY .npmrc package.json bun.lock ./
COPY packages/api-client/package.json packages/api-client/
COPY apps/login-miniapp/package.json apps/login-miniapp/
COPY apps/seller-dashboard/package.json apps/seller-dashboard/
RUN bun install --frozen-lockfile

COPY packages/api-client/ packages/api-client/
COPY apps/seller-dashboard/ apps/seller-dashboard/
RUN bun run --filter @sellbot/seller-dashboard build

FROM nginx:1.27-alpine
COPY apps/seller-dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/apps/seller-dashboard/dist /usr/share/nginx/html/dashboard
EXPOSE 80
