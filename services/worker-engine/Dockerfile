FROM golang:1.26-alpine AS builder
WORKDIR /build
RUN apk add --no-cache protobuf-dev git bash
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.5 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
COPY proto/ ./proto/
COPY scripts/gen-proto-go.sh ./scripts/
COPY services/worker-engine/ ./services/worker-engine/
WORKDIR /build
ENV PATH="$PATH:/root/go/bin"
RUN bash scripts/gen-proto-go.sh
WORKDIR /build/services/worker-engine
RUN go mod tidy && CGO_ENABLED=0 go build -o /worker-engine ./cmd/engine

FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates
COPY --from=builder /worker-engine .
RUN mkdir -p /data
VOLUME ["/data"]
ENTRYPOINT ["./worker-engine"]
