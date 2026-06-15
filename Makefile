.PHONY: gen-proto gen-proto-python gen-proto-java gen-proto-go build build-local test up down logs publish-models publish-models-local

gen-proto: gen-proto-python gen-proto-go gen-proto-java

gen-proto-java:
	cd services/core && ./gradlew generateProto --no-daemon

gen-proto-go:
	bash scripts/gen-proto-go.sh

gen-proto-python:
	bash scripts/gen-proto-python.sh


build-local: gen-proto
	cd services/core && ./gradlew bootJar -x test --no-daemon
	cd services/worker-engine && go build -o worker-engine ./cmd/engine
	cd services/web && bun install && bun run build
	cd services/seller-bot && bun run lint

build:
	docker compose build

test: gen-proto
	cd services/core && ./gradlew test --no-daemon
	cd services/worker-engine && go test ./... -count=1
	cd services/matching && pip3 install ".[dev]" && pytest tests/ -q
	cd services/http-gateway && bun install --frozen-lockfile && bun run lint && bun test
	cd services/seller-bot && bun run lint && bun test

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

# MODELS_S3_* from .env; optional PUBLISH_ARGS=--skip-parity
publish-models:
	@test -n "$(MODELS_VERSION)" || (echo "Usage: make publish-models MODELS_VERSION=2026.06.15-1" >&2 && exit 1)
	cd services/matching && pip3 install -q ".[train]" && ./scripts/publish_models.sh $(MODELS_VERSION) $(PUBLISH_ARGS)

publish-models-local:
	@test -n "$(MODELS_VERSION)" || (echo "Usage: make publish-models-local MODELS_VERSION=dev-1" >&2 && exit 1)
	cd services/matching && pip3 install -q ".[train]" && ./scripts/publish_models.sh --local-only $(MODELS_VERSION) $(PUBLISH_ARGS)

demo-lead:
	@echo "Inject test message (set DEV_INJECT_MESSAGE in .env first)"
	docker compose restart worker-engine
