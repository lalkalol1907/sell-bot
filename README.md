# sell-bot

Telegram-система для продавцов: воркеры слушают чаты, Matching находит заявки, бот шлёт лиды.

## Стек

| Сервис | Язык |
|--------|------|
| Core | Kotlin + Spring Boot + gRPC + Flyway (JDK 24) |
| Worker Engine | Go 1.26 (gotd MTProto) |
| Matching | Python 3.14 + FastAPI + rapidfuzz |
| Seller Bot | TypeScript + grammY + **Bun 1.3.14** |

## Быстрый старт

```bash
cp .env.example .env
# BOT_TOKEN, TG_API_ID, TG_API_HASH

docker compose up -d --build
```

Сервисы:
- Core gRPC `:50051`, health `http://localhost:8080/actuator/health`
- Matching `http://localhost:8000/health`

## E2E демо (без MTProto)

1. Запустить стек, открыть бота → `/start`
2. `/add_product` → iPhone 16 → 79990 → RUB
3. В `.env` задать:
   ```
   DEV_INJECT_MESSAGE=куплю айфон 16
   OWNER_SELLER_ID=1
   SESSION_ENCRYPTION_KEY=<openssl rand -base64 32>
   ```
4. `docker compose restart worker-engine`
5. Бот пришлёт уведомление о лиде

## Добавление воркера (MTProto)

1. Задайте `TG_API_ID`, `TG_API_HASH`, `SESSION_ENCRYPTION_KEY` в `.env`
2. В боте: **Воркеры** → **Добавить воркера** (или `/add_worker`)
3. Введите телефон → код из Telegram → пароль 2FA (если есть)
4. **Воркеры** → выберите воркера → включите чаты в whitelist
5. Worker-engine подхватит сессию из БД и начнёт слушать выбранные чаты

Поток лидов: `worker-engine` → NATS `message.captured` → Matching → Core → NATS `lead.created` → Seller Bot.

## Тесты

```bash
make test
```

Покрытие по сервисам:

| Сервис | Фреймворк | Что тестируется |
|--------|-----------|-----------------|
| **Matching** | pytest (34 теста) | normalize, intent, matcher, dedup, process_message, /health |
| **Core** | JUnit 5 + Mockito (17 тестов) | CatalogService, LeadsService, WorkersService |
| **Worker Engine** | go test | crypto, listener, config, sessionstore, publisher, login |
| **Seller Bot** | bun test (15 тестов) | phone, validation, lead formatting, telegram links |

Перед тестами Go/Python нужны proto-стабы: `make gen-proto` (включено в `make test`).

## Локальная разработка

Требования для Core: **JDK 24** (Temurin).

```bash
# Proto stubs (обязательно перед go/py сборкой)
make gen-proto

# Core (Java proto stubs + jar)
cd services/core && ./gradlew generateProto bootJar -x test

# Worker Engine
cd services/worker-engine && go build -o worker-engine ./cmd/engine

# Seller Bot
cd services/seller-bot && bun install && bun run dev

# Matching tests
cd services/matching && pip install . pytest && pytest tests/
```

## Структура

```
sell-bot/
├── proto/
├── services/
│   ├── core/
│   ├── worker-engine/
│   ├── matching/
│   └── seller-bot/
├── deploy/
└── docker-compose.yml
```

## Деплой (VPS)

Как в MujahidMusicV4: тесты на каждый push/PR, сборка и деплой — только по тегу `v*`.

1. Настрой GitHub Secrets:
   - `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
   - `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`
   - `DEPLOY_DOTENV` — полный `.env` для продакшена (BOT_TOKEN, TG_API_ID, …)
   - опционально: `DEPLOY_SSH_KEY_PASSPHRASE`

2. Релиз:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. CI: test → build (4 образа в Docker Hub) → deploy (SSH) → GitHub Release

Образы: `{DOCKERHUB_USERNAME}/{repo}-core`, `-worker-engine`, `-matching`, `-seller-bot`

На сервере: `docker compose -f deploy/docker-compose.prod.yml up -d`

Подробный план: `../gb-plan.md`
