package login_test

import (
	"context"
	"testing"

	"github.com/sellbot/worker-engine/internal/login"
)

func TestManagerGetNotFound(t *testing.T) {
	mgr := login.NewManager(1, "hash", "key", nil)
	_, err := mgr.SubmitCode(context.Background(), "missing-id", "12345")
	if err != login.ErrLoginNotFound {
		t.Fatalf("expected ErrLoginNotFound, got %v", err)
	}
}

func TestManagerStartLoginRequiresConfig(t *testing.T) {
	mgr := login.NewManager(0, "", "", nil)
	_, err := mgr.StartLogin(context.Background(), 1, "+79991234567")
	if err == nil {
		t.Fatal("expected config error")
	}
}
