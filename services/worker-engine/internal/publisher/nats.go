package publisher

import (
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

type NATS struct {
	nc *nats.Conn
}

func Connect(url string) (*NATS, error) {
	nc, err := nats.Connect(url)
	if err != nil {
		return nil, err
	}
	return &NATS{nc: nc}, nil
}

func (n *NATS) Close() {
	n.nc.Close()
}

func (n *NATS) PublishCaptured(msg CapturedMessage) error {
	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}
	return n.nc.Publish("message.captured", data)
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
