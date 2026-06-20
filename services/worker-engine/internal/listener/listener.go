package listener

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"strconv"

	"github.com/gotd/td/session"
	"github.com/gotd/td/telegram"
	"github.com/gotd/td/telegram/updates"
	"github.com/gotd/td/tg"

	"github.com/sellbot/worker-engine/internal/config"
	"github.com/sellbot/worker-engine/internal/core"
	"github.com/sellbot/worker-engine/internal/metrics"
	"github.com/sellbot/worker-engine/internal/publisher"
	"github.com/sellbot/worker-engine/internal/sessionstore"
)

type Runtime struct {
	WorkerID      int64
	OwnerSellerID int64
	SessionData   []byte
	ChatTitles    map[int64]string
	SyncCh        chan struct{}
}

type Listener struct {
	cfg    config.Config
	core   *core.Client
	nats   *publisher.NATS
	mu     sync.RWMutex
	active map[int64]bool
}

func New(cfg config.Config, coreClient *core.Client, nats *publisher.NATS) *Listener {
	return &Listener{
		cfg:    cfg,
		core:   coreClient,
		nats:   nats,
		active: map[int64]bool{},
	}
}

func (l *Listener) Run(ctx context.Context, rt Runtime) error {
	if l.cfg.TgAPIID == 0 || l.cfg.TgAPIHash == "" {
		return fmt.Errorf("TG_API_ID and TG_API_HASH required for MTProto")
	}

	storage, err := l.sessionStorage(rt)
	if err != nil {
		return err
	}

	client := telegram.NewClient(l.cfg.TgAPIID, l.cfg.TgAPIHash, telegram.Options{
		SessionStorage: storage,
	})

	return client.Run(ctx, func(ctx context.Context) error {
		if err := l.refreshWhitelist(ctx, rt); err != nil {
			log.Printf("worker %d: whitelist refresh failed: %v", rt.WorkerID, err)
		}

		if err := l.syncDialogs(ctx, client.API(), rt); err != nil {
			log.Printf("worker %d: sync dialogs failed: %v", rt.WorkerID, err)
		}

		go l.dialogsSyncLoop(ctx, client.API(), rt)

		go l.whitelistLoop(ctx, rt)

		self, err := client.Self(ctx)
		if err != nil {
			return fmt.Errorf("self: %w", err)
		}
		_ = l.core.UpdateWorkerStatus(ctx, rt.WorkerID, "active")

		dispatcher := tg.NewUpdateDispatcher()
		dispatcher.OnNewMessage(func(ctx context.Context, entities tg.Entities, update *tg.UpdateNewMessage) error {
			return l.onMessage(ctx, rt, update.Message)
		})
		dispatcher.OnNewChannelMessage(func(ctx context.Context, entities tg.Entities, update *tg.UpdateNewChannelMessage) error {
			return l.onMessage(ctx, rt, update.Message)
		})

		gap := updates.New(updates.Config{Handler: dispatcher})
		log.Printf("worker %d: MTProto listener started (account %d)", rt.WorkerID, self.ID)
		return gap.Run(ctx, client.API(), self.ID, updates.AuthOptions{IsBot: self.Bot})
	})
}

func (l *Listener) sessionStorage(rt Runtime) (session.Storage, error) {
	if len(rt.SessionData) > 0 {
		return &sessionstore.MemoryStorage{Data: rt.SessionData}, nil
	}
	if l.cfg.WorkerSessionString != "" {
		return &sessionstore.MemoryStorage{Data: []byte(l.cfg.WorkerSessionString)}, nil
	}
	if _, err := os.Stat(l.cfg.WorkerSessionPath); err == nil {
		return &sessionstore.FileStorage{Path: l.cfg.WorkerSessionPath}, nil
	}
	return nil, fmt.Errorf("no session for worker %d", rt.WorkerID)
}

func (l *Listener) ShouldListen(chatID int64) bool {
	return l.shouldListen(chatID)
}

// SetActiveChats sets whitelist for tests and manual overrides.
func (l *Listener) SetActiveChats(active map[int64]bool) {
	l.mu.Lock()
	l.active = active
	l.mu.Unlock()
}

func (l *Listener) shouldListen(chatID int64) bool {
	l.mu.RLock()
	defer l.mu.RUnlock()
	if len(l.active) == 0 && l.cfg.ListenAllChats {
		return true
	}
	return l.active[chatID]
}

func (l *Listener) dialogsSyncLoop(ctx context.Context, api *tg.Client, rt Runtime) {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := l.syncDialogs(ctx, api, rt); err != nil {
				log.Printf("worker %d: periodic dialog sync failed: %v", rt.WorkerID, err)
			}
		case <-rt.SyncCh:
			if err := l.syncDialogs(ctx, api, rt); err != nil {
				log.Printf("worker %d: requested dialog sync failed: %v", rt.WorkerID, err)
			}
		}
	}
}

func (l *Listener) whitelistLoop(ctx context.Context, rt Runtime) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := l.refreshWhitelist(ctx, rt); err != nil {
				log.Printf("worker %d: whitelist refresh: %v", rt.WorkerID, err)
			}
		}
	}
}

func (l *Listener) refreshWhitelist(ctx context.Context, rt Runtime) error {
	ids, err := l.core.ListActiveChatIDs(ctx, rt.WorkerID, rt.OwnerSellerID)
	if err != nil {
		return err
	}
	l.mu.Lock()
	l.active = ids
	l.mu.Unlock()
	return nil
}

func (l *Listener) isActive(chatID int64) bool {
	l.mu.RLock()
	defer l.mu.RUnlock()
	return l.active[chatID]
}

func (l *Listener) onMessage(ctx context.Context, rt Runtime, msg tg.MessageClass) error {
	m, ok := msg.(*tg.Message)
	if !ok || m.Out || m.Message == "" {
		return nil
	}

	chatID := PeerID(m.PeerID)
	if chatID == 0 || !l.shouldListen(chatID) {
		return nil
	}

	authorID, authorUsername := ExtractAuthor(m)
	title := rt.ChatTitles[chatID]
	publishChatID := BotAPIChatID(m.PeerID)

	err := l.nats.PublishCaptured(publisher.CapturedMessage{
		SellerID:       rt.OwnerSellerID,
		WorkerID:       rt.WorkerID,
		ChatID:         publishChatID,
		MessageID:      int64(m.ID),
		AuthorID:       authorID,
		AuthorUsername: authorUsername,
		ChatTitle:      title,
		RawText:        m.Message,
	})
	if err != nil {
		log.Printf(
			"worker %d: capture publish failed chat=%d msg=%d: %v",
			rt.WorkerID, publishChatID, m.ID, err,
		)
		return err
	}

	metrics.MessagesCaptured.Inc()
	log.Printf(
		"worker %d: captured chat=%d msg=%d author=%d title=%q text=%q",
		rt.WorkerID, publishChatID, m.ID, authorID, title, TruncateForLog(m.Message, 120),
	)
	return nil
}

func TruncateForLog(text string, maxRunes int) string {
	runes := []rune(text)
	if maxRunes <= 0 || len(runes) <= maxRunes {
		return text
	}
	return string(runes[:maxRunes]) + "…"
}

func BotAPIChatID(peer tg.PeerClass) int64 {
	switch p := peer.(type) {
	case *tg.PeerChannel:
		id, err := strconv.ParseInt("-100"+strconv.FormatInt(p.ChannelID, 10), 10, 64)
		if err != nil {
			return p.ChannelID
		}
		return id
	case *tg.PeerChat:
		return -p.ChatID
	case *tg.PeerUser:
		return p.UserID
	default:
		return 0
	}
}

func PeerID(peer tg.PeerClass) int64 {
	switch p := peer.(type) {
	case *tg.PeerChannel:
		return p.ChannelID
	case *tg.PeerChat:
		return p.ChatID
	case *tg.PeerUser:
		return p.UserID
	default:
		return 0
	}
}

func ExtractAuthor(m *tg.Message) (int64, string) {
	if m.FromID == nil {
		return 0, ""
	}
	switch f := m.FromID.(type) {
	case *tg.PeerUser:
		return f.UserID, ""
	default:
		return 0, ""
	}
}

func ChatInfo(chat tg.ChatClass) (int64, string, string) {
	switch c := chat.(type) {
	case *tg.Channel:
		return c.ID, c.Title, "channel"
	case *tg.Chat:
		return c.ID, c.Title, "group"
	default:
		return 0, "", ""
	}
}

func IsAuthError(err error) bool {
	if err == nil {
		return false
	}
	s := err.Error()
	return strings.Contains(s, "AUTH_KEY") || strings.Contains(s, "SESSION_REVOKED") || strings.Contains(s, "USER_DEACTIVATED")
}
