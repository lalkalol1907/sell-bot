# sell-bot

Telegram-система для продавцов: userbot-воркеры слушают чаты, Matching находит заявки на покупку, seller-bot уведомляет продавца. Подключение воркеров — через Telegram Mini App (QR или телефон), без OTP в чате бота.

## Стек

| Сервис | Язык | Роль |
|--------|------|------|
| **Core** | Kotlin + Spring Boot + gRPC + Flyway (JDK 24) | Каталог, воркеры, лиды, сессии (PostgreSQL) |
| **Worker Engine** | Go 1.26 (gotd MTProto) | Слушатели чатов, MTProto login (gRPC) |
| **Matching** | Python 3.14 + FastAPI + rapidfuzz | Нормализация, intent, fuzzy match, dedup |
| **Seller Bot** | TypeScript + grammY + Bun 1.3.14 | UX продавца, уведомления о лидах |
| **Login Gateway** | TypeScript + Bun | Mini App UI + HTTP BFF (публичный HTTPS) |

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
            │  seller-bot   │   │   Mini App    │          │
            │  (grammY)     │──►│  (WebApp UI)  │          │
            └───────┬───────┘   └───────┬───────┘          │
                    │                   │ HTTPS REST       │
                    │ gRPC              ▼                   │
                    │           ┌───────────────┐          │
                    │           │ login-gateway │          │
                    │           │  (Bun BFF)    │          │
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
 Продавец        seller-bot       Mini App      login-gateway    worker-engine       core        Telegram
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
| **login-gateway** | Публичный HTTPS | Static Mini App, REST API, валидация `initData` |
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
| Login Gateway | `8081` | Mini App + REST API |
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
- Login Gateway: `http://localhost:8081/health`

---

## Добавление воркера (Mini App)

1. Задайте в `.env`: `TG_API_ID`, `TG_API_HASH`, `SESSION_ENCRYPTION_KEY`, `INTERNAL_GRPC_TOKEN`
2. `LOGIN_WEB_URL` — URL login-gateway (см. TLS ниже)
3. В боте: **Воркеры** → **Добавить воркера** → **Открыть подключение воркера**
4. В Mini App:
   - **QR** — сканировать в официальном Telegram (Настройки → Устройства)
   - **Телефон** — код и 2FA вводятся в форме WebApp
5. **Воркеры** → выбрать воркера → включить чаты в whitelist

### LOGIN_WEB_URL и TLS

Telegram WebApp требует HTTPS в проде.

1. Поддомен, например `login.example.com`
2. Reverse proxy (Caddy/nginx) → `login-gateway:8080`
3. BotFather → разрешить домен WebApp
4. `.env`: `LOGIN_WEB_URL=https://login.example.com`

Локально: `LOGIN_WEB_URL=http://localhost:8081` (вне Telegram) или ngrok/cloudflared на `8081`.

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
| Login Gateway | bun test | Telegram initData validation |

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

# Login Gateway (API + Mini App)
cd services/login-gateway/web && bun install && bun run build
cd services/login-gateway && bun install && bun run dev

# Seller Bot
cd services/seller-bot && bun install && bun run dev

# Matching
cd services/matching && pip install ".[dev]" && pytest tests/
```

---

## Структура репозитория

```
sell-bot/
├── proto/                    # gRPC контракты
├── scripts/                  # gen-proto-go.sh, gen-proto-python.sh
├── services/
│   ├── core/                 # Kotlin Spring, PostgreSQL, Flyway
│   ├── worker-engine/        # Go: listeners + login.Manager (gRPC)
│   ├── matching/             # Python: matcher pipeline
│   ├── seller-bot/           # grammY бот продавца
│   └── login-gateway/        # Bun BFF + web/ (Vite React Mini App)
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
| `BOT_TOKEN` | seller-bot, login-gateway | Telegram Bot API + валидация initData |
| `LOGIN_WEB_URL` | seller-bot | URL кнопки WebApp |
| `INTERNAL_GRPC_TOKEN` | core, worker-engine, login-gateway | Auth internal gRPC (metadata) |
| `TG_API_ID`, `TG_API_HASH` | worker-engine | Telegram API для MTProto |
| `SESSION_ENCRYPTION_KEY` | worker-engine | Шифрование session-строк воркеров |
| `CORE_GRPC_ADDR` | все gRPC-клиенты | Адрес Core |

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

CI: test → build (5 образов) → deploy (SSH) → GitHub Release

**Docker Hub образы:**
- `{user}/{repo}-core`
- `{user}/{repo}-worker-engine`
- `{user}/{repo}-matching`
- `{user}/{repo}-seller-bot`
- `{user}/{repo}-login-gateway`

На сервере:
```bash
docker compose -f deploy/docker-compose.prod.yml up -d
```

`login-gateway` в prod не пробрасывает порт наружу — только через reverse proxy с TLS.

Подробный продуктовый план: [`../gb-plan.md`](../gb-plan.md)
