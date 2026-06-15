FROM oven/bun:1.3.14-alpine AS builder
WORKDIR /app
ARG VITE_BOT_USERNAME=
ARG VITE_MINIAPP_URL=/miniapp/
ENV VITE_BOT_USERNAME=$VITE_BOT_USERNAME
ENV VITE_MINIAPP_URL=$VITE_MINIAPP_URL
COPY package.json ./
RUN bun install
COPY . .
RUN bun run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html/dashboard
EXPOSE 80
