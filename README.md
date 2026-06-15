# sell-bot

Telegram-система для продавцов: userbot-воркеры слушают чаты, Matching находит заявки на покупку, seller-bot уведомляет продавца. Подключение воркеров — через Telegram Mini App (QR или телефон), без OTP в чате бота.

## Стек

| Сервис | Язык | Роль |
|--------|------|------|
| **Core** | Kotlin + Spring Boot + gRPC + Flyway (JDK 24) | Каталог, воркеры, лиды, сессии (PostgreSQL) |
| **Worker Engine** | Go 1.26 (gotd MTProto) | Слушатели чатов, MTProto login (gRPC) |
| **Matching** | Python 3.14 + FastAPI + rapidfuzz | Нормализация, intent, fuzzy match, dedup |
| **Seller Bot** | TypeScript + grammY + Bun 1.3.14 | UX продавца, уведомления о лидах |
| **HTTP Gateway** | Bun 1.3.14 + Hono + gRPC | REST API: seller dashboard + login Mini App |
| **Login Mini App** | HTML/CSS/JS + nginx | Статика Mini App, прокси `/api/` → http-gateway |
| **Seller Dashboard** | Vite + React + nginx | Веб-кабинет продавца, прокси `/api/` → http-gateway |

Инфраструктура: **PostgreSQL**, **Redis**, **NATS JetStream**.

---

## Архитектура

### Общая схема

```
                         ┌─────────────────────────────────────┐
                         │         Продавец (Telegram)         │
                         └──────────────┬──────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   │
            ┌───────────────┐   ┌───────────────┐          │
            │  seller-bot   │   │ login-miniapp │          │
            │  (grammY)     │──►│ nginx + React │          │
            └───────┬───────┘   └───────┬───────┘          │
                    │                   │ /api/            │
                    │ gRPC              ▼                   │
                    │           ┌───────────────┐          │
                    │           │ http-gateway  │          │
                    │           │  (Bun + Hono) │          │
                    │           └───┬───────┬───┘          │
                    │               │       │              │
                    │         gRPC  │       │ gRPC         │
                    │    catalog    │       │ worker_login │
                    │               │       │              │
                    ▼               ▼       ▼              │
            ┌───────────────────────────────────┐          │
            │              core (Kotlin)         │          │
            │         gRPC :50051 + Flyway       │          │
            └───────────────────┬───────────────┘          │
                                │                          │
                                ▼                          │
                         ┌────────────┐                    │
                         │ PostgreSQL │                    │
                         └────────────┘                    │
                                                            │
    seller-dashboard ──► nginx + React (JWT cookie auth)   │
         /api/ ─────────► http-gateway (тот же API)        │
    ┌───────────────┐         NATS          ┌────────────┴───┐
    │ worker-engine │ ───publish──────────► │    matching    │
    │  (Go/gotd)    │ ◄──subscribe───────── │   (Python)     │
    └───────┬───────┘                       └───────┬────────┘
            │                                       │
            │ MTProto                               │ gRPC + Redis
            ▼                                       ▼
    ┌───────────────┐                       ┌───────────────┐
    │   Telegram    │                       │     core      │
    │  (чаты, QR)   │                       └───────────────┘

    seller-bot ──NATS subscribe──► lead.created
    seller-bot ──Redis──► сессии FSM
```

### Поток лидов

```
 Telegram чат          worker-engine          NATS           matching            core           seller-bot         Продавец
      │                     │                  │                │                 │                 │                │
      │  новое сообщение    │                  │                │                 │                 │                │
      │────────────────────►│                  │                │                 │                 │                │
      │                     │  whitelist       │                │                 │                 │                │
      │                     │  message.captured│                │                 │                 │                │
      │                     │─────────────────►│                │                 │                 │                │
      │                     │                  │  consume       │                 │                 │                │
      │                     │                  │───────────────►│                 │                 │                │
      │                     │                  │                │ get_seller      │                 │                │
      │                     │                  │                │ list_products   │                 │                │
      │                     │                  │                │────────────────►│                 │                │
      │                     │                  │                │ match + dedup   │                 │                │
      │                     │                  │                │ create_lead     │                 │                │
      │                     │                  │                │────────────────►│                 │                │
      │                     │                  │  lead.created  │                 │                 │                │
      │                     │                  │◄───────────────│                 │                 │                │
      │                     │                  │                │                 │  subscribe      │                │
      │                     │                  │─────────────────────────────────────────────────►│                │
      │                     │                  │                │                 │  карточка лида  │                │
      │                     │                  │                │                 │────────────────────────────────►│
```

1. **worker-engine** слушает выбранные чаты (MTProto userbot).
2. Сообщение публикуется в NATS (`message.captured`).
3. **matching** сопоставляет текст с каталогом продавца, дедуплицирует, создаёт лид в Core.
4. Событие `lead.created` → **seller-bot** шлёт карточку продавцу.

### Поток подключения воркера (Mini App)

OTP и 2FA **не проходят через чат бота** — только через WebApp или QR в официальном Telegram.

```
 Продавец        seller-bot       Mini App      http-gateway    worker-engine       core        Telegram
     │                │               │               │                │              │              │
     │ Добавить       │               │               │                │              │              │
     │ воркера        │               │               │                │              │              │
     │───────────────►│               │               │                │              │              │
     │                │ кнопка WebApp │               │                │              │              │
     │◄───────────────│               │               │                │              │              │
     │ открыть форму  │               │               │                │              │              │
     │───────────────────────────────►│               │                │              │              │
     │                │               │ POST /session │                │              │              │
     │                │               │──────────────►│ GetSellerByTgId│              │              │
     │                │               │               │───────────────►│              │              │
     │                │               │               │                │              │              │
     │  ─── вариант QR ───            │               │                │              │              │
     │                │               │ POST /qr/start│                │              │              │
     │                │               │──────────────►│ StartQRLogin   │              │              │
     │                │               │               │───────────────►│ qrlogin.Auth │              │
     │                │               │               │                │─────────────►│              │
     │                │               │◄─ qr_url ─────│                │              │              │
     │ сканировать QR │               │               │                │              │              │
     │─────────────────────────────────────────────────────────────────────────────────────────────►│
     │                │               │ GET /status   │                │              │              │
     │                │               │──────────────►│ GetLoginStatus │              │              │
     │                │               │               │───────────────►│              │              │
     │                │               │               │                │              │              │
     │  ─── вариант Телефон ───       │               │                │              │              │
     │                │               │ POST /phone   │                │              │              │
     │                │               │──────────────►│ StartLogin     │              │              │
     │                │               │               │───────────────►│ SendCode     │              │
     │                │               │               │                │─────────────►│              │
     │                │               │ POST /code    │                │              │              │
     │                │               │──────────────►│ SubmitCode     │              │              │
     │                │               │ POST /password│                │              │              │
     │                │               │──────────────►│ SubmitPassword │              │              │
     │                │               │               │                │              │              │
     │                │               │               │ CreateWorker   │              │              │
     │                │               │               │───────────────►│─────────────►│              │
     │                │               │ sendData OK   │                │              │              │
     │                │◄──────────────│               │                │              │              │
     │◄───────────────│ воркер OK     │               │                │              │              │
```

**Границы ответственности:**

| Сервис | Сеть | Что делает |
|--------|------|------------|
| **login-miniapp** | Публичный HTTPS (nginx) | Static Mini App, прокси `/api/` → http-gateway |
| **seller-dashboard** | Публичный HTTPS (nginx) | Static dashboard, прокси `/api/` → http-gateway |
| **http-gateway** | Internal only | REST API, JWT + initData, gRPC → core / worker-engine |
| **worker-engine** | Только internal | MTProto login, listener-воркеры, gRPC `:50053` |
| **seller-bot** | Telegram Bot API | Точка входа (кнопка WebApp), приём результата |

Внутренний gRPC защищён metadata `x-internal-grpc-token` (`INTERNAL_GRPC_TOKEN`).

### Proto / gRPC контракты

| Файл | Сервисы |
|------|---------|
| `proto/catalog.proto` | Core — продавцы, каталог |
| `proto/workers.proto` | Core — воркеры, чаты, сессии |
| `proto/leads.proto` | Core — лиды, статистика |
| `proto/matching.proto` | Matching — ProcessMessage |
| `proto/worker_login.proto` | Worker Engine — phone/QR login, poll статуса |

---

## Порты (локальный docker compose)

| Сервис | Порт | Назначение |
|--------|------|------------|
| Core gRPC | `50051` | gRPC API |
| Core HTTP | `8080` | Actuator health |
| Matching gRPC | `50052` | gRPC (опционально) |
| Matching HTTP | `8000` | `/health` |
| Login Mini App | `8081` | nginx: `/miniapp/` + `/api/` proxy |
| Seller Dashboard | `8082` | nginx: `/dashboard/` + `/api/` proxy |
| HTTP Gateway | — | internal `:3000` (только через nginx фронтов) |
| Worker Engine login gRPC | `50053` | internal only (не проброшен в prod) |
| PostgreSQL | `5432` | |
| Redis | `6379` | |
| NATS | `4222` | |

---

## Быстрый старт

```bash
cp .env.example .env
# Обязательно: BOT_TOKEN, TG_API_ID, TG_API_HASH, SESSION_ENCRYPTION_KEY, INTERNAL_GRPC_TOKEN

docker compose up -d --build
```

Проверка:
- Core: `http://localhost:8080/actuator/health`
- Matching: `http://localhost:8000/health`
- Login Mini App: `http://localhost:8081/health`
- Seller Dashboard: `http://localhost:8082/health`

---

## Добавление воркера (Mini App)

1. Задайте в `.env`: `TG_API_ID`, `TG_API_HASH`, `SESSION_ENCRYPTION_KEY`, `INTERNAL_GRPC_TOKEN`
2. `LOGIN_WEB_URL` — URL login-miniapp (см. TLS ниже)
3. В боте: **Воркеры** → **Добавить воркера** → **Открыть подключение воркера**
4. В Mini App:
   - **QR** — сканировать в официальном Telegram (Настройки → Устройства)
   - **Телефон** — код и 2FA вводятся в форме WebApp
5. **Воркеры** → выбрать воркера → включить чаты в whitelist

### LOGIN_WEB_URL и TLS

Telegram WebApp требует HTTPS в проде.

Prod-стек включает **Caddy** (`deploy/docker/caddy/Caddyfile`) — auto-TLS через Let's Encrypt и балансировку входящего трафика:

| Домен (`*.env`) | Куда проксирует | Назначение |
|-----------------|-----------------|------------|
| `LOGIN_DOMAIN` | `login-miniapp:80` (dynamic LB) | Mini App (`/miniapp/`) + `/api/` |
| `APP_DOMAIN` | `seller-dashboard:80` (dynamic LB) | Dashboard (`/dashboard/`) + `/api/` |
| `BOT_DOMAIN` | `seller-bot:8080` (dynamic LB) | Webhook Telegram + health/metrics |

1. Три поддомена, например `login.example.com`, `app.example.com`, `bot.example.com`
2. DNS A/AAAA каждого домена → VPS; порты **80** и **443** открыты
3. В `.env`: `LOGIN_DOMAIN`, `APP_DOMAIN`, `BOT_DOMAIN`, `ACME_EMAIL`
4. BotFather → разрешить домен WebApp для `LOGIN_DOMAIN`
5. `.env`:
   ```env
   LOGIN_WEB_URL=https://login.example.com/miniapp/
   CORS_ORIGINS=https://login.example.com,https://app.example.com
   BOT_TRANSPORT=webhook
   WEBHOOK_URL=https://bot.example.com/telegram/webhook
   ```

Масштабирование за Caddy (Docker DNS → все реплики сервиса):
```bash
docker compose -f deploy/docker-compose.prod.yml up -d \
  --scale login-miniapp=2 \
  --scale seller-dashboard=2 \
  --scale seller-bot=3
```

Локально: `LOGIN_WEB_URL=http://localhost:8081/miniapp/` (вне Telegram) или ngrok/cloudflared на `8081`.

---

## E2E демо (без MTProto)

1. Запустить стек, в боте → `/start`
2. `/add_product` → iPhone 16 → 79990 → RUB
3. В `.env`:
   ```
   DEV_INJECT_MESSAGE=куплю айфон 16
   OWNER_SELLER_ID=1
   SESSION_ENCRYPTION_KEY=<openssl rand -base64 32>
   ```
4. `docker compose restart worker-engine`
5. Бот пришлёт уведомление о лиде

---

## Тесты

```bash
make test
```

| Сервис | Фреймворк | Что тестируется |
|--------|-----------|-----------------|
| Matching | pytest | normalize, intent, matcher, dedup, process_message |
| Core | JUnit 5 + Mockito | CatalogService, LeadsService, WorkersService, InternalGrpcAuth |
| Worker Engine | go test | crypto, listener, login (phone + QR gRPC), grpcauth |
| Seller Bot | bun test | utils, worker-add web_app_data |
| HTTP Gateway | bun test | Telegram initData, login routing |

Перед тестами Go/Python: `make gen-proto` (включено в `make test`).

---

## Локальная разработка

Требования: **JDK 24** (Core), **Go 1.26**, **Bun 1.3.14**, **Python 3.14**.

```bash
make gen-proto

# Core
cd services/core && ./gradlew generateProto bootJar -x test

# Worker Engine
cd services/worker-engine && go build -o worker-engine ./cmd/engine

# Web monorepo (Mini App + Dashboard)
cd services/web && bun install
bun run dev:miniapp    # :5173/miniapp/
bun run dev:dashboard  # :5174/dashboard/

# HTTP Gateway
cd services/http-gateway && bun install && bun run dev

# Seller Bot
cd services/seller-bot && bun install && bun run dev

# Matching
cd services/matching && pip install ".[dev]" && pytest tests/ -m "not integration"
```

### NLP v2 (matching)

Пайплайн распознавания: `normalize_v2` → `product_gate` (fuzzy + semantic/Qdrant) → `intent_classifier` (ML + эвристики) → scoring.

| Flag | Default | Описание |
|------|---------|----------|
| `NLP_V2_ENABLED` | `false` | Master switch v2 pipeline |
| `NLP_V2_SEMANTIC` | `true` | Qdrant semantic match |
| `NLP_V2_INTENT_ML` | `true` | ML intent head |
| `NLP_V2_NORMALIZE` | `false` | pymorphy3 + razdel normalize |

**Варианты (память / цвет):** если в сообщении указаны объём или цвет, `product_gate` понижает similarity товарам без этих атрибутов или с несовпадением (`VARIANT_*_MULT` в `.env`). В каталоге можно задать `storage_gb` и `color` у товара или положить их в `title`/`keywords` (например `iPhone 16 Pro 256GB Black`).

Golden regression suite: `services/matching/data/recognition_cases.yaml` (80+ кейсов). В CI гоняются только fast-кейсы (`pytest -m "not integration"`); semantic/Qdrant и обучение intent — локально.

```bash
cd services/matching
pytest tests/ -m "not integration" -q
python scripts/eval_recognition.py          # локально, с моделью
pytest tests/ -m integration -q             # Qdrant + semantic golden + train smoke
```

Добавить кейс при багрепорте: запись в `recognition_cases.yaml` → `pytest tests/test_recognition_golden.py -k <id>`.

Переобучение intent: `python scripts/train_intent.py` / `python scripts/retrain_intent.py`.

---

## Мониторинг (Grafana stack)

В `docker-compose.yml` включён полный стек из `monitoring/`:

| Сервис | Порт | Назначение |
|--------|------|------------|
| **Grafana** | 3000 | Дашборды (host, docker, sellbot) |
| **Prometheus** | 9090 | Метрики сервисов и blackbox-проверки |
| **Loki** | 3100 | Хранение логов |
| **Promtail** | — | Сбор логов Docker-контейнеров |
| **node-exporter** | 9100 | Метрики хоста |
| **cadvisor** | 8083 | Метрики контейнеров |
| **blackbox-exporter** | 9115 | HTTP health-пробы |

Дашборды лежат в `monitoring/grafana/provisioning/dashboards/json/`:
- `host.json` — CPU/RAM/диск хоста
- `docker.json` — контейнеры Docker
- `sellbot.json` — лиды, спам-фильтр, уведомления

Логин Grafana: `admin` / `admin` (или `GRAFANA_ADMIN_*` из `monitoring/.env.example`).

Переменные спам-фильтра matching:
- `MIN_MESSAGE_CHARS` (по умолчанию 8)
- `MAX_MESSAGE_CHARS` (по умолчанию 2000)

---

## Структура репозитория

```
sell-bot/
├── proto/                    # gRPC контракты
├── monitoring/               # Prometheus, Loki, Grafana, дашборды
├── scripts/                  # gen-proto-*.sh
├── services/
│   ├── core/                 # Kotlin Spring, PostgreSQL, Flyway
│   ├── worker-engine/        # Go: listeners + login.Manager (gRPC)
│   ├── matching/             # Python: matcher pipeline
│   ├── seller-bot/           # grammY бот продавца
│   ├── http-gateway/         # Bun API (seller + login endpoints)
│   └── web/                  # Bun monorepo: apps/login-miniapp, apps/seller-dashboard
├── deploy/
│   └── docker-compose.prod.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Переменные окружения

Ключевые (полный список — `.env.example`):

| Переменная | Сервис | Назначение |
|------------|--------|------------|
| `BOT_TOKEN` | seller-bot, http-gateway | Telegram Bot API + валидация initData |
| `JWT_SECRET` | http-gateway | Подпись JWT для seller dashboard |
| `CORS_ORIGINS` | http-gateway | Origins фронтов (8081, 8082) |
| `BOT_USERNAME` | http-gateway, seller-dashboard | Telegram Login Widget |
| `LOGIN_WEB_URL` | seller-bot | URL кнопки WebApp |
| `BOT_TRANSPORT` | seller-bot | `polling` (dev, 1 реплика) или `webhook` (prod, scale) |
| `WEBHOOK_URL` | seller-bot | Публичный URL webhook (обязателен при `webhook`) |
| `WEBHOOK_SECRET` | seller-bot | `X-Telegram-Bot-Api-Secret-Token` (обязателен при `webhook`) |
| `WEBHOOK_PATH` | seller-bot | Путь на HTTP-сервере (по умолчанию `/telegram/webhook`) |
| `HTTP_PORT` | seller-bot | HTTP: health, metrics, webhook (по умолчанию `8080`) |
| `REDIS_URL` | http-gateway, seller-bot | Rate limit / FSM / login routes |
| `WORKER_LOGIN_GRPC_ADDR` | http-gateway | Один или несколько `host:port` через запятую |
| `LOGIN_ROUTE_TTL_SEC` | http-gateway | TTL привязки `login_id` → worker-engine (сек) |
| `INTERNAL_GRPC_TOKEN` | core, worker-engine, http-gateway | Auth internal gRPC (metadata) |
| `TG_API_ID`, `TG_API_HASH` | worker-engine | Telegram API для MTProto |
| `SESSION_ENCRYPTION_KEY` | worker-engine | Шифрование session-строк воркеров |
| `CORE_GRPC_ADDR` | все gRPC-клиенты | Адрес Core |
| `NATS_URL` | core, matching, seller-bot, worker-engine | JetStream |
| `MIN_MESSAGE_CHARS` / `MAX_MESSAGE_CHARS` | matching | Фильтр спама по длине |

### seller-bot: polling vs webhook

| Режим | Env | Реплики | Когда |
|-------|-----|---------|-------|
| **polling** | `BOT_TRANSPORT=polling` | **1** | локальная разработка |
| **webhook** | `BOT_TRANSPORT=webhook` + `WEBHOOK_URL` + `WEBHOOK_SECRET` | **N** | продакшен за LB/ingress |

В webhook-режиме:
- Telegram шлёт updates на `WEBHOOK_URL` → балансировщик → любая реплика seller-bot
- FSM-сессии в **Redis** — общие для всех реплик
- NATS consumers (`lead.created`, `worker.status`) с **deliver_group** — очередь между репликами
- `setWebhook` идемпотентен; при scale можно оставить `WEBHOOK_REGISTER_ON_STARTUP=true` на всех pod'ах

Пример prod:
```yaml
seller-bot:
  deploy:
    replicas: 3
  environment:
    BOT_TRANSPORT: webhook
    WEBHOOK_URL: https://bot.example.com/telegram/webhook
    WEBHOOK_PATH: /telegram/webhook
    WEBHOOK_SECRET: <random>
    HTTP_PORT: 8080
```

### Core и http-gateway: горизонтальный скейл

**Core** — несколько реплик безопасны:
- Outbox `notifications` забирается через `FOR UPDATE SKIP LOCKED` (статус `processing`)
- Зависшие `processing` возвращаются в `pending` через `stale-minutes`

**http-gateway** — несколько реплик безопасны:
- Rate limit в **Redis** (общий для всех pod'ов)
- При старте login сохраняется `login_id → worker-engine` в Redis
- Последующие code/password/status идут на тот же engine

`WORKER_LOGIN_GRPC_ADDR` поддерживает список через запятую:
```env
WORKER_LOGIN_GRPC_ADDR=worker-engine-0:50053,worker-engine-1:50053
```

---

## Деплой (VPS)

Как в MujahidMusicV4: тесты на push/PR, сборка и деплой — только по тегу `v*`.

**GitHub Secrets:**
- `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`
- `DEPLOY_DOTENV` — полный `.env` для продакшена

**Релиз:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

CI: test → build (7 образов) → deploy (SSH) → GitHub Release

**Docker Hub образы:**
- `{user}/{repo}-core`
- `{user}/{repo}-worker-engine`
- `{user}/{repo}-matching`
- `{user}/{repo}-seller-bot`
- `{user}/{repo}-http-gateway`
- `{user}/{repo}-login-miniapp`
- `{user}/{repo}-seller-dashboard`

На сервере:
```bash
docker compose -f deploy/docker-compose.prod.yml up -d
```

**Caddy** слушает `:80`/`:443`, выпускает TLS-сертификаты и проксирует на фронты и webhook (см. `LOGIN_DOMAIN`, `APP_DOMAIN`, `BOT_DOMAIN` в `.env.example`).

`http-gateway` в prod не пробрасывает порт наружу — только через nginx фронтов с TLS.

Подробный продуктовый план: [`../gb-plan.md`](../gb-plan.md)
