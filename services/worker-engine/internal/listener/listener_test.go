package listener_test

import (
	"errors"
	"testing"

	"github.com/gotd/td/tg"
	"github.com/sellbot/worker-engine/internal/config"
	"github.com/sellbot/worker-engine/internal/listener"
)

func TestPeerID(t *testing.T) {
	tests := []struct {
		name string
		peer tg.PeerClass
		want int64
	}{
		{"channel", &tg.PeerChannel{ChannelID: 123}, 123},
		{"chat", &tg.PeerChat{ChatID: 456}, 456},
		{"user", &tg.PeerUser{UserID: 789}, 789},
		{"nil", nil, 0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := listener.PeerID(tt.peer); got != tt.want {
				t.Fatalf("PeerID() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestExtractAuthor(t *testing.T) {
	authorID, username := listener.ExtractAuthor(&tg.Message{
		FromID: &tg.PeerUser{UserID: 42},
	})
	if authorID != 42 || username != "" {
		t.Fatalf("got authorID=%d username=%q", authorID, username)
	}

	authorID, _ = listener.ExtractAuthor(&tg.Message{})
	if authorID != 0 {
		t.Fatalf("expected 0 for nil FromID, got %d", authorID)
	}
}

func TestChatInfo(t *testing.T) {
	id, title, typ := listener.ChatInfo(&tg.Channel{ID: 10, Title: "News"})
	if id != 10 || title != "News" || typ != "channel" {
		t.Fatalf("channel info mismatch: %d %q %q", id, title, typ)
	}

	id, title, typ = listener.ChatInfo(&tg.Chat{ID: 20, Title: "Group"})
	if id != 20 || title != "Group" || typ != "group" {
		t.Fatalf("group info mismatch")
	}
}

func TestShouldListen(t *testing.T) {
	l := listener.New(config.Config{ListenAllChats: true}, nil, nil)
	if !l.ShouldListen(100) {
		t.Fatal("expected listen all when whitelist empty")
	}

	l.SetActiveChats(map[int64]bool{100: true})
	if !l.ShouldListen(100) {
		t.Fatal("expected active chat")
	}
	if l.ShouldListen(200) {
		t.Fatal("expected inactive chat blocked")
	}
}

func TestBotAPIChatID(t *testing.T) {
	tests := []struct {
		name string
		peer tg.PeerClass
		want int64
	}{
		{"channel", &tg.PeerChannel{ChannelID: 1234567890}, -1001234567890},
		{"chat", &tg.PeerChat{ChatID: 456}, -456},
		{"user", &tg.PeerUser{UserID: 789}, 789},
		{"nil", nil, 0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := listener.BotAPIChatID(tt.peer); got != tt.want {
				t.Fatalf("BotAPIChatID() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestTruncateForLog(t *testing.T) {
	if got := listener.TruncateForLog("hello", 10); got != "hello" {
		t.Fatalf("got %q", got)
	}
	long := "куплю айфон 16 pro max с большим объёмом памяти"
	got := listener.TruncateForLog(long, 20)
	if len([]rune(got)) > 21 {
		t.Fatalf("expected truncation, got %q", got)
	}
}

func TestIsAuthError(t *testing.T) {
	if !listener.IsAuthError(errors.New("AUTH_KEY_UNREGISTERED")) {
		t.Fatal("expected auth error")
	}
	if !listener.IsAuthError(errors.New("SESSION_REVOKED")) {
		t.Fatal("expected session revoked")
	}
	if listener.IsAuthError(errors.New("network timeout")) {
		t.Fatal("expected benign error")
	}
	if listener.IsAuthError(nil) {
		t.Fatal("nil should not be auth error")
	}
}
