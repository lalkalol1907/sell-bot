FROM oven/bun:1.3.14-alpine AS web-builder
WORKDIR /build/web
COPY services/login-gateway/web/.npmrc services/login-gateway/web/package.json ./
RUN bun install
COPY services/login-gateway/web/ ./
RUN bun run build

FROM oven/bun:1.3.14-alpine AS api-deps
WORKDIR /app
COPY services/login-gateway/.npmrc services/login-gateway/package.json ./
RUN bun install

FROM oven/bun:1.3.14-alpine AS release
WORKDIR /app
COPY proto ./proto
COPY --from=api-deps /app/node_modules ./node_modules
COPY services/login-gateway/package.json services/login-gateway/tsconfig.json ./
COPY services/login-gateway/src ./src
COPY --from=web-builder /build/web/dist ./web/dist

ENV PORT=8080
EXPOSE 8080
CMD ["bun", "run", "src/main.ts"]
