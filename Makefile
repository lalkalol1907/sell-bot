.PHONY: gen-proto gen-proto-python gen-proto-java gen-proto-go gen-proto-ruby build build-local test up down logs

gen-proto: gen-proto-python gen-proto-go gen-proto-java gen-proto-ruby

gen-proto-java:
	cd services/core && ./gradlew generateProto --no-daemon

gen-proto-go:
	bash scripts/gen-proto-go.sh

gen-proto-python:
	bash scripts/gen-proto-python.sh

gen-proto-ruby:
	bash scripts/gen-proto-ruby.sh

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
	cd services/http-gateway && bundle install && bundle exec rspec
	cd services/seller-bot && bun run lint && bun test

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

demo-lead:
	@echo "Inject test message (set DEV_INJECT_MESSAGE in .env first)"
	docker compose restart worker-engine
