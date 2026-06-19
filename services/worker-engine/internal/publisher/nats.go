package publisher

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/nats-io/nats.go"
)

type CapturedMessage struct {
	SellerID       int64  `json:"seller_id"`
	WorkerID       int64  `json:"worker_id"`
	ChatID         int64  `json:"chat_id"`
	MessageID      int64  `json:"message_id"`
	AuthorID       int64  `json:"author_id"`
	AuthorUsername string `json:"author_username"`
	ChatTitle      string `json:"chat_title"`
	RawText        string `json:"raw_text"`
}

type WorkerStatusEvent struct {
	WorkerID       int64  `json:"worker_id"`
	OwnerSellerID  int64  `json:"owner_seller_id"`
	Status         string `json:"status"`
	Phone          string `json:"phone,omitempty"`
}

type SyncChatsRequest struct {
	WorkerID int64 `json:"worker_id"`
}

type NATS struct {
	nc *nats.Conn
	js nats.JetStreamContext
}

func Connect(url string) (*NATS, error) {
	nc, err := nats.Connect(url)
	if err != nil {
		return nil, err
	}
	js, err := nc.JetStream()
	if err != nil {
		nc.Close()
		return nil, err
	}
	n := &NATS{nc: nc, js: js}
	if err := n.ensureStream(); err != nil {
		nc.Close()
		return nil, err
	}
	return n, nil
}

func (n *NATS) ensureStream() error {
	_, err := n.js.StreamInfo("SELLBOT")
	if err == nil {
		return nil
	}
	_, err = n.js.AddStream(&nats.StreamConfig{
		Name:     "SELLBOT",
		Subjects: []string{"lead.created", "worker.status", "message.captured"},
		Storage:  nats.FileStorage,
		MaxAge:   7 * 24 * time.Hour,
	})
	return err
}

func (n *NATS) Close() {
	n.nc.Close()
}

func (n *NATS) publish(subject string, data []byte) error {
	_, err := n.js.Publish(subject, data)
	return err
}

func (n *NATS) PublishCaptured(msg CapturedMessage) error {
	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}
	return n.publish("message.captured", data)
}

func (n *NATS) PublishWorkerStatus(evt WorkerStatusEvent) error {
	data, err := json.Marshal(evt)
	if err != nil {
		return err
	}
	return n.publish("worker.status", data)
}

func (n *NATS) PublishSyncChatsRequest(workerID int64) error {
	data, err := json.Marshal(SyncChatsRequest{WorkerID: workerID})
	if err != nil {
		return err
	}
	return n.nc.Publish("worker.sync_chats", data)
}

func (n *NATS) SubscribeSyncChats(ctx context.Context, handler func(workerID int64)) error {
	sub, err := n.nc.Subscribe("worker.sync_chats", func(msg *nats.Msg) {
		var req SyncChatsRequest
		if err := json.Unmarshal(msg.Data, &req); err != nil {
			log.Printf("invalid worker.sync_chats payload: %v", err)
			return
		}
		if req.WorkerID == 0 {
			return
		}
		handler(req.WorkerID)
	})
	if err != nil {
		return err
	}
	go func() {
		<-ctx.Done()
		if err := sub.Unsubscribe(); err != nil {
			log.Printf("nats unsubscribe worker.sync_chats: %v", err)
		}
	}()
	return nil
}

func (n *NATS) PublishDevMessage(sellerID, workerID int64, raw string, chatID, authorID int64, chatTitle, authorUsername string) error {
	if raw == "" {
		return nil
	}
	msg := CapturedMessage{
		SellerID:       sellerID,
		WorkerID:       workerID,
		ChatID:         chatID,
		MessageID:      time.Now().Unix(),
		AuthorID:       authorID,
		AuthorUsername: authorUsername,
		ChatTitle:      chatTitle,
		RawText:        raw,
	}
	if err := n.PublishCaptured(msg); err != nil {
		return err
	}
	log.Printf("published dev message to message.captured: %q", raw)
	return nil
}

func ParseIDs(sellerID, workerID, chatID, authorID string, defaults ...int64) (int64, int64, int64, int64, error) {
	def := func(i int) int64 {
		if i < len(defaults) {
			return defaults[i]
		}
		return 0
	}
	parse := func(s string, fallback int64) (int64, error) {
		if s == "" {
			return fallback, nil
		}
		var v int64
		_, err := fmt.Sscan(s, &v)
		return v, err
	}
	s, err := parse(sellerID, def(0))
	if err != nil {
		return 0, 0, 0, 0, err
	}
	w, err := parse(workerID, def(1))
	if err != nil {
		return 0, 0, 0, 0, err
	}
	c, err := parse(chatID, def(2))
	if err != nil {
		return 0, 0, 0, 0, err
	}
	a, err := parse(authorID, def(3))
	if err != nil {
		return 0, 0, 0, 0, err
	}
	return s, w, c, a, nil
}
