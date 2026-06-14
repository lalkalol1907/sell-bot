package login_test

import (
	"context"
	"testing"

	workerloginpb "github.com/sellbot/worker-engine/internal/gen/workerlogin"
	"github.com/sellbot/worker-engine/internal/grpcauth"
	"github.com/sellbot/worker-engine/internal/login"
)

func TestGRPCServerRejectsInvalidToken(t *testing.T) {
	mgr := login.NewManager(0, "", "", nil)
	srv := login.NewGRPCServer(mgr, "secret")
	ctx := grpcauth.IncomingContext(context.Background(), "wrong")

	resp, err := srv.StartLogin(ctx, &workerloginpb.StartLoginRequest{
		OwnerSellerId: 1,
		Phone:         "+79991234567",
	})
	if err != nil {
		t.Fatalf("StartLogin returned error: %v", err)
	}
	if resp.Status != login.StatusError {
		t.Fatalf("expected error status, got %q", resp.Status)
	}
}

func TestGRPCServerAllowsMatchingToken(t *testing.T) {
	mgr := login.NewManager(0, "", "", nil)
	srv := login.NewGRPCServer(mgr, "secret")
	ctx := grpcauth.IncomingContext(context.Background(), "secret")

	resp, err := srv.StartLogin(ctx, &workerloginpb.StartLoginRequest{
		OwnerSellerId: 1,
		Phone:         "+79991234567",
	})
	if err != nil {
		t.Fatalf("StartLogin returned error: %v", err)
	}
	if resp.Status != login.StatusError {
		t.Fatalf("expected config error (not auth), got %q message=%q", resp.Status, resp.Message)
	}
	if resp.Message == "unauthorized" {
		t.Fatal("should not reject valid token")
	}
}

func TestGRPCServerSubmitCodeRequiresAuth(t *testing.T) {
	mgr := login.NewManager(0, "", "", nil)
	srv := login.NewGRPCServer(mgr, "secret")

	resp, err := srv.SubmitCode(context.Background(), &workerloginpb.SubmitCodeRequest{
		LoginId: "x",
		Code:    "12345",
	})
	if err != nil {
		t.Fatalf("SubmitCode returned error: %v", err)
	}
	if resp.Message != "unauthorized" {
		t.Fatalf("expected unauthorized, got %q", resp.Message)
	}
}

func TestGRPCServerGetLoginStatusNotFound(t *testing.T) {
	mgr := login.NewManager(0, "", "", nil)
	srv := login.NewGRPCServer(mgr, "secret")
	ctx := grpcauth.IncomingContext(context.Background(), "secret")

	resp, err := srv.GetLoginStatus(ctx, &workerloginpb.GetLoginStatusRequest{LoginId: "missing"})
	if err != nil {
		t.Fatalf("GetLoginStatus returned error: %v", err)
	}
	if resp.Status != login.StatusError {
		t.Fatalf("expected error status, got %q", resp.Status)
	}
}
