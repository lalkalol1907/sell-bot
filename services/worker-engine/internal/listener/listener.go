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

	workerspb "github.com/sellbot/worker-engine/internal/gen/workers"
	"github.com/sellbot/worker-engine/internal/config"
	"github.com/sellbot/worker-engine/internal/core"
	"github.com/sellbot/worker-engine/internal/publisher"
	"github.com/sellbot/worker-engine/internal/sessionstore"
)

type Runtime struct {
	WorkerID      int64
	OwnerSellerID int64
	SessionData   []byte
	ChatTitles    map[int64]string
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

	return l.nats.PublishCaptured(publisher.CapturedMessage{
		SellerID:       rt.OwnerSellerID,
		WorkerID:       rt.WorkerID,
		ChatID:         publishChatID,
		MessageID:      int64(m.ID),
		AuthorID:       authorID,
		AuthorUsername: authorUsername,
		ChatTitle:      title,
		RawText:        m.Message,
	})
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

func (l *Listener) syncDialogs(ctx context.Context, api *tg.Client, rt Runtime) error {
	result, err := api.MessagesGetDialogs(ctx, &tg.MessagesGetDialogsRequest{
		OffsetPeer: &tg.InputPeerEmpty{},
		Limit:      100,
	})
	if err != nil {
		return err
	}

	var dialogs []tg.ChatClass
	switch d := result.(type) {
	case *tg.MessagesDialogs:
		dialogs = d.Chats
	case *tg.MessagesDialogsSlice:
		dialogs = d.Chats
	default:
		return nil
	}

	chats := make([]*workerspb.MonitoredChat, 0, len(dialogs))
	for _, chat := range dialogs {
		id, title, typ := ChatInfo(chat)
		if id == 0 {
			continue
		}
		rt.ChatTitles[id] = title
		chats = append(chats, &workerspb.MonitoredChat{
			WorkerId: rt.WorkerID,
			ChatId:   id,
			Title:    title,
			Type:     typ,
			IsActive: false,
		})
	}

	if len(chats) == 0 {
		return nil
	}
	synced, err := l.core.SyncChats(ctx, rt.WorkerID, chats)
	if err != nil {
		return err
	}
	log.Printf("worker %d: synced %d chats", rt.WorkerID, synced)
	return nil
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
