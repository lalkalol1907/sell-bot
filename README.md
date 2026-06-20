# sell-bot

Telegram-система для продавцов: userbot-воркеры слушают чаты, Matching находит заявки на покупку, seller-bot уведомляет продавца. Подключение воркеров — через Telegram Mini App (QR или телефон), без OTP в чате бота.

## Стек

| Сервис | Язык | Роль |
|--------|------|------|
| **Core** | Kotlin + Spring Boot + gRPC + Flyway (JDK 25) | Каталог, воркеры, лиды, REST `/api/v1` для фронтов, PostgreSQL |
| **Worker Engine** | Go 1.26 (gotd MTProto) | Слушатели чатов, MTProto login (gRPC) |
| **Matching** | Python 3.14 + FastAPI + rapidfuzz | Нормализация, intent, fuzzy match, dedup |
| **Seller Bot** | TypeScript + grammY + Bun 1.3.14 | UX продавца, уведомления о лидах |
| **Login Mini App** | Vue 3 + Vite + Bun | Mini App подключения воркера, nginx прокси `/api/` → core |
| **Seller Dashboard** | Vue 3 + Vite + Bun | Веб-кабинет продавца, nginx прокси `/api/` → core |

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
            │  (grammY)     │──►│ nginx + Vue   │          │
            └───────┬───────┘   └───────┬───────┘          │
                    │                   │ /api/            │
                    │ gRPC              ▼                   │
                    │           ┌───────────────┐          │
                    │           │     core      │          │
                    │           │ REST :8080    │          │
                    │           │ gRPC :50051   │          │
                    │           └───┬───────┬───┘          │
                    │               │       │              │
                    │               │       │ gRPC         │
                    │               │       │ worker_login │
                    └──────────────►│       ▼              │
                                    │  PostgreSQL          │
                                    │  Redis (login routes)│
                                    └──────────────────────┘
                                                            │
    seller-dashboard ──► nginx + Vue (JWT cookie auth)   │
         /api/ ─────────► core :8080 (тот же REST API)        │
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
 Продавец        seller-bot       Mini App         core           worker-engine      Telegram
     │                │               │               │                │              │
     │ Добавить       │               │               │                │              │
     │ воркера        │               │               │                │              │
     │───────────────►│               │               │                │              │
     │                │ кнопка WebApp │               │                │              │
     │◄───────────────│               │               │                │              │
     │ открыть форму  │               │               │                │              │
     │───────────────────────────────►│               │                │              │
     │                │               │ POST /session │                │              │
     │                │               │──────────────►│ initData auth  │              │
     │                │               │               │                │              │
     │  ─── вариант QR ───            │               │                │              │
     │                │               │ POST /qr/start│                │              │
     │                │               │──────────────►│ StartQRLogin   │              │
     │                │               │               │───────────────►│ qrlogin.Auth │
     │                │               │               │                │─────────────►│
     │                │               │◄─ qr_url ─────│                │              │
     │ сканировать QR │               │               │                │              │
     │──────────────────────────────────────────────────────────────────────────────►│
     │                │               │ GET /status   │                │              │
     │                │               │──────────────►│ GetLoginStatus │              │
     │                │               │               │───────────────►│              │
     │                │               │               │                │              │
     │  ─── вариант Телефон ───       │               │                │              │
     │                │               │ POST /phone   │                │              │
     │                │               │──────────────►│ StartLogin     │              │
     │                │               │               │───────────────►│ SendCode     │
     │                │               │               │                │─────────────►│
     │                │               │ POST /code    │                │              │
     │                │               │──────────────►│ SubmitCode     │              │
     │                │               │ POST /password│                │              │
     │                │               │──────────────►│ SubmitPassword │              │
     │                │               │               │                │              │
     │                │               │               │ CreateWorker   │              │
     │                │               │               │◄───────────────│              │
     │                │               │ sendData OK   │                │              │
     │                │◄──────────────│               │                │              │
     │◄───────────────│ воркер OK     │               │                │              │
```

**Границы ответственности:**

| Сервис | Сеть | Что делает |
|--------|------|------------|
| **login-miniapp** | Публичный HTTPS (nginx) | Vue Mini App, прокси `/api/` → core |
| **seller-dashboard** | Публичный HTTPS (nginx) | Static dashboard, прокси `/api/` → core |
| **core** | Internal HTTP + gRPC | REST `/api/v1` (JWT, initData, handoff), domain logic, PostgreSQL, Redis |
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
| Core gRPC | `50051` | gRPC API (matching, seller-bot, worker-engine) |
| Core HTTP | `8080` | REST `/api/v1`, `/health`, Actuator `/actuator/*` |
| Matching gRPC | `50052` | gRPC (опционально) |
| Matching HTTP | `8000` | `/health` |
| Login Mini App | `8081` | nginx: `/miniapp/` + `/api/` → core |
| Seller Dashboard | `8082` | nginx: `/dashboard/` + `/api/` → core |
| Worker Engine login gRPC | `50053` | internal only (не проброшен в prod) |
| PostgreSQL | `5432` | |
| Redis | `6379` | |
| NATS | `4222` | |

---

## Быстрый старт

```bash
cp .env.example .env
# Обязательно: BOT_TOKEN, JWT_SECRET, TG_API_ID, TG_API_HASH, SESSION_ENCRYPTION_KEY, INTERNAL_GRPC_TOKEN

docker compose up -d --build
```

Проверка:
- Core: `http://localhost:8080/actuator/health`, REST: `http://localhost:8080/health`
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

Prod-стек включает **Caddy** (`caddy/Caddyfile`) — auto-TLS через Let's Encrypt и балансировку входящего трафика:

| Домен (`*.env`) | Куда проксирует | Назначение |
|-----------------|-----------------|------------|
| `LOGIN_DOMAIN` | `login-miniapp:80` (dynamic LB) | Mini App (`/miniapp/`) + `/api/` |
| `APP_DOMAIN` | `seller-dashboard:80` (dynamic LB) | Dashboard (`/dashboard/`) + `/api/` |
| `BOT_DOMAIN` | `seller-bot:8080` (dynamic LB) | Webhook Telegram + health/metrics |
| `GRAFANA_DOMAIN` | `grafana:3000` | Grafana (дашборды и логи) |

1. Четыре поддомена, например `login.example.com`, `app.example.com`, `bot.example.com`, `grafana.example.com`
2. DNS A/AAAA каждого домена → VPS; порты **80** и **443** открыты
3. В `.env`: `LOGIN_DOMAIN`, `APP_DOMAIN`, `BOT_DOMAIN`, `GRAFANA_DOMAIN`, `ACME_EMAIL`, `GRAFANA_ADMIN_PASSWORD`
4. BotFather (два разных домена — не путать):
   - **Mini App** (`login-miniapp`): Bot Settings → Menu Button / Web App URL → `https://<LOGIN_DOMAIN>/miniapp/`
   - **Login Widget** (дашборд): `/setdomain` → выбрать бота → указать **только хост** `APP_DOMAIN` (например `app.example.com`, без `https://`). У бота один домен для виджета; если указать `LOGIN_DOMAIN`, вход на дашборде не сработает.
5. В боте выполнить `/start` (без этого `POST /api/v1/auth/telegram` вернёт 401).
6. `.env`:
   ```env
   LOGIN_WEB_URL=https://login.example.com/miniapp/
   CORS_ORIGINS=https://login.example.com,https://app.example.com
   BOT_TRANSPORT=webhook
   WEBHOOK_URL=https://bot.example.com/telegram/webhook
   ```

Масштабирование за Caddy (Docker DNS → все реплики сервиса):
```bash
docker compose -f docker-compose.prod.yml up -d \
  --scale core=2 \
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
| Core | JUnit 5 + Mockito | CatalogService, LeadsService, WorkersService, InternalGrpcAuth, TelegramAuth, JWT |
| Worker Engine | go test | crypto, listener, login (phone + QR gRPC), grpcauth |
| Seller Bot | bun test | utils, worker-add web_app_data |

Перед тестами Go/Python: `make gen-proto` (включено в `make test`).

---

## Локальная разработка

Требования: **JDK 25** (Core), **Go 1.26**, **Bun 1.3.14**, **Python 3.14**.

```bash
make gen-proto

# Core (gRPC :50051 + REST :8080)
cd services/core && ./gradlew bootRun

# Worker Engine
cd services/worker-engine && go build -o worker-engine ./cmd/engine

# Web monorepo (Mini App + Dashboard; dev-серверы проксируют /api/ на core :8080)
cd services/web && bun install
bun run dev:miniapp    # :5173/miniapp/
bun run dev:dashboard  # :5174/dashboard/

# Seller Bot
cd services/seller-bot && bun install && bun run dev

# Matching
cd services/matching && pip install ".[dev]" && pytest tests/ -m "not integration"
```

### Matching pipeline

Пайплайн: `normalize` → `product_gate` (fuzzy + semantic/Qdrant) → `intent_classifier` (ML) → scoring.

Пороги (`fuzzy_min_score`, `semantic_min_score`) загружаются из `semantic_thresholds.json` в model bundle.

**Варианты (память / цвет):** если в сообщении указаны объём или цвет, `product_gate` понижает similarity товарам без этих атрибутов или с несовпадением (`VARIANT_*_MULT` в `.env`).

Golden regression suite: `services/matching/data/recognition_cases.yaml` (80+ кейсов). В CI гоняются fast-кейсы (`pytest -m "not integration"`).

**Модели (ONNX + S3):** runtime использует `fastembed` без PyTorch. Артефакты: `intent.joblib`, `semantic_thresholds.json`, ONNX embedding.

```bash
# обучить prod-модель (datasets → calibrate → train → pytest gate)
make train

# собрать bundle + parity + golden gate + upload в S3
make publish MODELS_VERSION=2026.06.19-1
```

| Env | Описание |
|-----|----------|
| `MODELS_SKIP_S3` | `true` — не качать из S3 (local dev) |
| `MODELS_S3_ENDPOINT` | URL S3-compatible API |
| `MODELS_S3_BUCKET` / `MODELS_S3_PREFIX` | bucket и префикс |
| `MODELS_S3_VERSION` | пин версии; пусто → `latest.json` |
| `MODELS_LOCAL_DIR` | volume для кэша (`/data/models`) |
| `EMBEDDING_MODEL_DIR` | выставляется bootstrap после sync |

При смене версии embedding bundle — **reindex Qdrant** (lazy reindex в indexer подхватит по catalog hash).

```bash
pytest tests/ -m integration -q   # parity / Qdrant — локально
```

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

Blackbox-пробы (`monitoring/prometheus/blackbox-targets.yml`): health всех сервисов, включая `core:8080/health` и `core:8080/actuator/health`.

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
│   ├── core/                 # Kotlin Spring, PostgreSQL, Flyway, REST /api/v1
│   ├── worker-engine/        # Go: listeners + login.Manager (gRPC)
│   ├── matching/             # Python: matcher pipeline
│   ├── seller-bot/           # grammY бот продавца
│   └── web/                  # Bun monorepo: apps/login-miniapp, apps/seller-dashboard
├── caddy/Caddyfile           # prod TLS / reverse proxy
├── docker-compose.prod.yml   # prod-стек (образы из Docker Hub)
├── docker-compose.yml        # локальная разработка
├── Makefile
└── .env.example
```

---

## Переменные окружения

Ключевые (полный список — `.env.example`):

| Переменная | Сервис | Назначение |
|------------|--------|------------|
| `BOT_TOKEN` | seller-bot, core | Telegram Bot API + валидация initData |
| `JWT_SECRET` | core | Подпись JWT для seller dashboard |
| `CORS_ORIGINS` | core | Origins фронтов (8081, 8082) |
| `BOT_USERNAME` | seller-dashboard | Telegram Login Widget |
| `LOGIN_WEB_URL` | seller-bot, core | URL кнопки WebApp и handoff dashboard → mini app |
| `SELLBOT_SECURE_COOKIES` | core | `true` в prod (Secure flag для JWT cookie) |
| `BOT_TRANSPORT` | seller-bot | `polling` (dev, 1 реплика) или `webhook` (prod, scale) |
| `WEBHOOK_URL` | seller-bot | Публичный URL webhook (обязателен при `webhook`) |
| `WEBHOOK_SECRET` | seller-bot | `X-Telegram-Bot-Api-Secret-Token` (обязателен при `webhook`) |
| `WEBHOOK_PATH` | seller-bot | Путь на HTTP-сервере (по умолчанию `/telegram/webhook`) |
| `HTTP_PORT` | seller-bot | HTTP: health, metrics, webhook (по умолчанию `8080`) |
| `REDIS_URL` | core, seller-bot | Rate limit / FSM / login routes |
| `WORKER_LOGIN_GRPC_ADDR` | core | Один или несколько `host:port` через запятую |
| `LOGIN_ROUTE_TTL_SEC` | core | TTL привязки `login_id` → worker-engine (сек) |
| `INTERNAL_GRPC_TOKEN` | core, worker-engine | Auth internal gRPC (metadata) |
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

### Core: горизонтальный скейл

**Core** — несколько реплик безопасны:
- Outbox `notifications` забирается через `FOR UPDATE SKIP LOCKED` (статус `processing`)
- Зависшие `processing` возвращаются в `pending` через `stale-minutes`
- REST API (`/api/v1`): rate limit и login routing в **Redis** (общий для всех реплик)
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
- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH` (корень проекта на сервере, напр. `/opt/sell-bot`)
- `DEPLOY_DOTENV` — полный `.env` для продакшена

**Релиз:**
```bash
git tag v1.0.0
git push origin v1.0.0
```

CI: test → build (6 образов) → deploy (SSH) → GitHub Release

**Docker Hub образы** (отдельного HTTP-gateway больше нет — REST в `core`):
- `{user}/{repo}-core`
- `{user}/{repo}-worker-engine`
- `{user}/{repo}-matching`
- `{user}/{repo}-seller-bot`
- `{user}/{repo}-login-miniapp`
- `{user}/{repo}-seller-dashboard`

На сервере в `$DEPLOY_PATH` (корень проекта):

```
/opt/sell-bot/
├── docker-compose.prod.yml
├── caddy/Caddyfile
├── monitoring/
└── .env
```

```bash
cd /opt/sell-bot
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d \
  --scale "core=${CORE_REPLICAS:-2}" \
  --scale "matching=${MATCHING_REPLICAS:-2}" \
  --scale "seller-bot=${SELLER_BOT_REPLICAS:-2}" \
  --scale "login-miniapp=${LOGIN_MINIAPP_REPLICAS:-2}" \
  --scale "seller-dashboard=${SELLER_DASHBOARD_REPLICAS:-2}"
```

Число реплик задаётся в `.env` (`CORE_REPLICAS`, `SELLER_BOT_REPLICAS`, … — см. `.env.example`). В compose также прописаны `deploy.update_config` (rolling, `start-first`) и `rollback_config`; на VPS без Swarm rolling выполняется через `pull` + `up --scale` (по одному образу за деплой CI). **worker-engine** — всегда 1 реплика: несколько реплик дублируют MTProto-слушателей для всех workers.

После обновления с версии с `http-gateway`: подтяните новые `docker-compose.prod.yml` и `monitoring/`, удалите старый контейнер (`docker compose ... rm -sf http-gateway`), пересоберите **core**, **login-miniapp**, **seller-dashboard**. Содержимое `DEPLOY_DOTENV` менять не нужно — те же `JWT_SECRET`, `CORS_ORIGINS`, `BOT_TOKEN` теперь читает `core`.

**Caddy** слушает `:80`/`:443`, выпускает TLS-сертификаты и проксирует на фронты, webhook и Grafana (см. `LOGIN_DOMAIN`, `APP_DOMAIN`, `BOT_DOMAIN`, `GRAFANA_DOMAIN` в `.env.example`).

REST API core в prod не пробрасывается наружу — только через nginx фронтов (`/api/` → `core:8080`) с TLS.

Подробный продуктовый план: [`../gb-plan.md`](../gb-plan.md)
