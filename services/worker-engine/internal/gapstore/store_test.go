package gapstore_test

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/gotd/td/telegram/updates"
	"github.com/sellbot/worker-engine/internal/gapstore"
)

func TestStoreStateRoundTrip(t *testing.T) {
	dir := t.TempDir()
	store, err := gapstore.Open(dir, 42)
	if err != nil {
		t.Fatal(err)
	}

	ctx := context.Background()
	state := updates.State{Pts: 10, Qts: 20, Date: 30, Seq: 40}
	if err := store.SetState(ctx, 100, state); err != nil {
		t.Fatal(err)
	}

	reloaded, err := gapstore.Open(dir, 42)
	if err != nil {
		t.Fatal(err)
	}
	got, found, err := reloaded.GetState(ctx, 100)
	if err != nil || !found {
		t.Fatalf("GetState() found=%v err=%v", found, err)
	}
	if got != state {
		t.Fatalf("state mismatch: %+v", got)
	}
}

func TestSetStateClearsChannels(t *testing.T) {
	dir := t.TempDir()
	store, err := gapstore.Open(dir, 1)
	if err != nil {
		t.Fatal(err)
	}

	ctx := context.Background()
	if err := store.SetState(ctx, 1, updates.State{Pts: 1}); err != nil {
		t.Fatal(err)
	}
	if err := store.SetChannelPts(ctx, 1, 999, 5); err != nil {
		t.Fatal(err)
	}
	if err := store.SetState(ctx, 1, updates.State{Pts: 2}); err != nil {
		t.Fatal(err)
	}

	_, found, err := store.GetChannelPts(ctx, 1, 999)
	if err != nil {
		t.Fatal(err)
	}
	if found {
		t.Fatal("expected channel pts cleared after SetState")
	}
}

func TestAccessHashPersistence(t *testing.T) {
	dir := t.TempDir()
	store, err := gapstore.Open(dir, 7)
	if err != nil {
		t.Fatal(err)
	}

	ctx := context.Background()
	if err := store.SetChannelAccessHash(ctx, 1, 123, 456789); err != nil {
		t.Fatal(err)
	}

	reloaded, err := gapstore.Open(dir, 7)
	if err != nil {
		t.Fatal(err)
	}
	hash, found, err := reloaded.GetChannelAccessHash(ctx, 1, 123)
	if err != nil || !found || hash != 456789 {
		t.Fatalf("hash=%d found=%v err=%v", hash, found, err)
	}
}

func TestStoreCreatesFile(t *testing.T) {
	dir := t.TempDir()
	store, err := gapstore.Open(dir, 3)
	if err != nil {
		t.Fatal(err)
	}
	if err := store.SetChannelAccessHash(context.Background(), 1, 10, 20); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "worker-3.json")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("expected file at %s: %v", path, err)
	}
}
