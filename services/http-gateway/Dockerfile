FROM oven/bun:1.3.14-alpine AS base
WORKDIR /app

FROM base AS install
COPY services/http-gateway/.npmrc services/http-gateway/package.json services/http-gateway/bun.lock ./
RUN bun install --frozen-lockfile

FROM base AS release
COPY proto ./proto
COPY --from=install /app/node_modules ./node_modules
COPY services/http-gateway/.npmrc services/http-gateway/package.json services/http-gateway/bun.lock services/http-gateway/tsconfig.json ./
COPY services/http-gateway/src ./src

ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

CMD ["bun", "run", "src/main.ts"]
