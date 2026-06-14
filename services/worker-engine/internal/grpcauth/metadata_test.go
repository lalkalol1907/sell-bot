package grpcauth_test

import (
	"context"
	"testing"

	"github.com/sellbot/worker-engine/internal/grpcauth"
	"google.golang.org/grpc/metadata"
)

func TestOutgoingAndIncomingContext(t *testing.T) {
	ctx := grpcauth.OutgoingContext(context.Background(), "secret")
	md, ok := metadata.FromOutgoingContext(ctx)
	if !ok {
		t.Fatal("expected outgoing metadata")
	}
	vals := md.Get(grpcauth.MetadataKey)
	if len(vals) != 1 || vals[0] != "secret" {
		t.Fatalf("unexpected metadata: %v", vals)
	}

	inCtx := grpcauth.IncomingContext(context.Background(), "secret")
	if got := grpcauth.TokenFromIncoming(inCtx); got != "secret" {
		t.Fatalf("TokenFromIncoming() = %q", got)
	}
}

func TestEmptyTokenLeavesContextUnchanged(t *testing.T) {
	ctx := grpcauth.OutgoingContext(context.Background(), "")
	if _, ok := metadata.FromOutgoingContext(ctx); ok {
		t.Fatal("expected no outgoing metadata for empty token")
	}
}
