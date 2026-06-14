FROM oven/bun:1.3.14-alpine AS base
WORKDIR /app

FROM base AS install
COPY services/seller-bot/package.json services/seller-bot/bun.lock ./
RUN bun install --frozen-lockfile

FROM base AS release
COPY proto ./proto
COPY --from=install /app/node_modules ./node_modules
COPY services/seller-bot/package.json services/seller-bot/bun.lock services/seller-bot/tsconfig.json ./
COPY services/seller-bot/src ./src

CMD ["bun", "run", "src/main.ts"]
