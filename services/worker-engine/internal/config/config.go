package config

import (
	"os"
	"strconv"
)

type Config struct {
	TgAPIID              int
	TgAPIHash            string
	SessionEncryptionKey string
	InternalGRPCSecret   string
	CoreGRPCAddr         string
	MatchingGRPCAddr     string
	NatsURL              string
	WorkerSessionString  string
	WorkerSessionPath    string
	UpdatesStateDir      string
	WorkerID             int64
	OwnerSellerID        int64
	DevInjectMessage     string
	ListenAllChats       bool
}

func Load() Config {
	return Config{
		TgAPIID:              envInt("TG_API_ID", 0),
		TgAPIHash:            os.Getenv("TG_API_HASH"),
		SessionEncryptionKey: os.Getenv("SESSION_ENCRYPTION_KEY"),
		InternalGRPCSecret:   os.Getenv("INTERNAL_GRPC_TOKEN"),
		CoreGRPCAddr:         envOr("CORE_GRPC_ADDR", "core:50051"),
		MatchingGRPCAddr:     envOr("MATCHING_GRPC_ADDR", "matching:50052"),
		NatsURL:              envOr("NATS_URL", "nats://nats:4222"),
		WorkerSessionString:  os.Getenv("WORKER_SESSION_STRING"),
		WorkerSessionPath:    envOr("WORKER_SESSION_PATH", "/data/session.json"),
		UpdatesStateDir:      envOr("UPDATES_STATE_DIR", "/data/updates-state"),
		WorkerID:             envInt64("WORKER_ID", 1),
		OwnerSellerID:        envInt64("OWNER_SELLER_ID", 1),
		DevInjectMessage:     os.Getenv("DEV_INJECT_MESSAGE"),
		ListenAllChats:       envOr("LISTEN_ALL_CHATS", "true") == "true",
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envInt(key string, fallback int) int {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return fallback
	}
	return n
}

func envInt64(key string, fallback int64) int64 {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.ParseInt(v, 10, 64)
	if err != nil {
		return fallback
	}
	return n
}
