package sessionstore_test

import (
	"context"
	"errors"
	"testing"

	"github.com/gotd/td/session"
	"github.com/sellbot/worker-engine/internal/sessionstore"
)

func TestMemoryStorageRoundTrip(t *testing.T) {
	store := &sessionstore.MemoryStorage{}
	data := []byte(`{"session":"data"}`)
	if err := store.StoreSession(context.Background(), data); err != nil {
		t.Fatal(err)
	}
	got, err := store.LoadSession(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != string(data) {
		t.Fatalf("got %q want %q", got, data)
	}
}

func TestMemoryStorageEmpty(t *testing.T) {
	store := &sessionstore.MemoryStorage{}
	_, err := store.LoadSession(context.Background())
	if !errors.Is(err, session.ErrNotFound) {
		t.Fatalf("expected ErrNotFound, got %v", err)
	}
}

func TestMemoryStorageCopyOnStore(t *testing.T) {
	store := &sessionstore.MemoryStorage{}
	original := []byte("abc")
	if err := store.StoreSession(context.Background(), original); err != nil {
		t.Fatal(err)
	}
	original[0] = 'z'
	got, _ := store.LoadSession(context.Background())
	if got[0] == 'z' {
		t.Fatal("storage should copy bytes on store")
	}
}

