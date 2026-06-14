package config_test

import (
	"testing"

	"github.com/sellbot/worker-engine/internal/config"
)

func TestLoadDefaults(t *testing.T) {
	t.Setenv("TG_API_ID", "")
	t.Setenv("CORE_GRPC_ADDR", "")
	t.Setenv("WORKER_ID", "")
	t.Setenv("OWNER_SELLER_ID", "")
	t.Setenv("LISTEN_ALL_CHATS", "")

	cfg := config.Load()
	if cfg.CoreGRPCAddr != "core:50051" {
		t.Fatalf("CoreGRPCAddr = %q", cfg.CoreGRPCAddr)
	}
	if cfg.WorkerID != 1 {
		t.Fatalf("WorkerID = %d", cfg.WorkerID)
	}
	if !cfg.ListenAllChats {
		t.Fatal("expected ListenAllChats true by default")
	}
}

func TestLoadFromEnv(t *testing.T) {
	t.Setenv("TG_API_ID", "12345")
	t.Setenv("TG_API_HASH", "hash")
	t.Setenv("WORKER_ID", "7")
	t.Setenv("OWNER_SELLER_ID", "3")
	t.Setenv("LISTEN_ALL_CHATS", "false")

	cfg := config.Load()
	if cfg.TgAPIID != 12345 {
		t.Fatalf("TgAPIID = %d", cfg.TgAPIID)
	}
	if cfg.TgAPIHash != "hash" {
		t.Fatalf("TgAPIHash = %q", cfg.TgAPIHash)
	}
	if cfg.WorkerID != 7 || cfg.OwnerSellerID != 3 {
		t.Fatalf("worker ids mismatch")
	}
	if cfg.ListenAllChats {
		t.Fatal("expected ListenAllChats false")
	}
}

func TestLoadInvalidIntFallback(t *testing.T) {
	t.Setenv("TG_API_ID", "not-a-number")
	cfg := config.Load()
	if cfg.TgAPIID != 0 {
		t.Fatalf("expected 0 fallback, got %d", cfg.TgAPIID)
	}
}
