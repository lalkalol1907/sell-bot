.PHONY: gen-proto gen-proto-python gen-proto-java gen-proto-go build build-local test up down logs train publish

define matching_run
	cd services/matching && \
	if [ -x .venv/bin/pip ]; then \
		.venv/bin/pip install -q ".[train]" && \
		.venv/bin/python -m app.training.cli $(1); \
	else \
		pip3 install -q ".[train]" && \
		python3 -m app.training.cli $(1); \
	fi
endef

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
	cd services/matching && pip3 install -e ".[dev]" && pytest tests/ -q
	cd services/seller-bot && bun run lint && bun test

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

train:
	@$(call matching_run,train)

publish:
	@test -n "$(MODELS_VERSION)" || (echo "Usage: make publish MODELS_VERSION=2026.06.19-1" >&2 && exit 1)
	@$(call matching_run,publish --version $(MODELS_VERSION))

demo-lead:
	@echo "Inject test message (set DEV_INJECT_MESSAGE in .env first)"
	docker compose restart worker-engine
