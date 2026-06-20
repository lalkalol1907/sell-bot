# Web monorepo

Bun workspaces: login-miniapp и seller-dashboard на Vite + Vue, один `bun.lock`, **отдельные Docker-образы и деплои**.

`.npmrc` — копия [`services/seller-bot/.npmrc`](../seller-bot/.npmrc) (обязателен для `bun install` локально и в Docker).

```
services/web/
├── package.json          # workspaces root
├── bun.lock
├── apps/
│   ├── login-miniapp/    # Mini App (Vue + Vite) → nginx :8081, /miniapp/
│   └── seller-dashboard/ # Dashboard (Vue + Vite) → nginx :8082, /dashboard/
```

## Локальная разработка

```bash
cd services/web
bun install

# Mini App (http://localhost:5173/miniapp/)
bun run dev:miniapp

# Dashboard (http://localhost:5174/dashboard/)
bun run dev:dashboard

# Собрать оба
bun run build
```

## Отдельные Docker-образы

Build context всегда **корень монорепо** (`services/web`), Dockerfile — внутри app.

### login-miniapp

```bash
docker build \
  -f apps/login-miniapp/Dockerfile \
  -t sellbot-login-miniapp \
  .
```

### seller-dashboard

```bash
docker build \
  -f apps/seller-dashboard/Dockerfile \
  --build-arg VITE_BOT_USERNAME=your_bot \
  --build-arg VITE_MINIAPP_URL=https://login.example.com/miniapp/ \
  -t sellbot-seller-dashboard \
  .
```

### docker compose (как в проекте)

```yaml
login-miniapp:
  build:
    context: ./services/web
    dockerfile: apps/login-miniapp/Dockerfile
  ports:
    - "8081:80"

seller-dashboard:
  build:
    context: ./services/web
    dockerfile: apps/seller-dashboard/Dockerfile
    args:
      VITE_BOT_USERNAME: ${BOT_USERNAME}
      VITE_MINIAPP_URL: ${LOGIN_WEB_URL}
  ports:
    - "8082:80"
```

## Prod: два независимых деплоя

CI собирает **два образа** из одного репо (`login-miniapp`, `seller-dashboard` в matrix).

На VPS можно:

**Вариант A — оба сервиса в одном compose** (как `docker-compose.prod.yml`):

```bash
docker compose -f docker-compose.prod.yml up -d login-miniapp seller-dashboard
```

**Вариант B — разные хосты / поддомены:**

```bash
# Сервер 1: только Mini App (Telegram WebApp)
docker run -d -p 443:80 \
  -e ... \
  sellbot-login-miniapp:latest
# Caddy (в docker-compose.prod.yml) → login.example.com → login-miniapp:80

# Сервер 2: только dashboard
docker run -d -p 443:80 \
  sellbot-seller-dashboard:latest
# Caddy (в docker-compose.prod.yml) → app.example.com → seller-dashboard:80
```

**Вариант C — обновить только один фронт:**

```bash
# Новый релиз затронул только dashboard
docker pull user/sellbot-seller-dashboard:v1.2.0
docker compose up -d seller-dashboard

# miniapp не трогаем
```

Оба контейнера проксируют `/api/` → `core:8080`; API один, фронты независимы.
