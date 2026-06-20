package listener

import (
	"context"
	"log"

	"github.com/gotd/td/telegram/query/dialogs"
	"github.com/gotd/td/telegram/updates"
	"github.com/gotd/td/tg"

	workerspb "github.com/sellbot/worker-engine/internal/gen/workers"
)

const dialogsBatchSize = 100

func chatFromElem(elem dialogs.Elem) (int64, string, string) {
	switch p := elem.Peer.(type) {
	case *tg.InputPeerChannel:
		if ch, ok := elem.Entities.Channel(p.ChannelID); ok {
			return ChatInfo(ch)
		}
		return p.ChannelID, "", "channel"
	case *tg.InputPeerChat:
		if ch, ok := elem.Entities.Chat(p.ChatID); ok {
			return ChatInfo(ch)
		}
		return p.ChatID, "", "group"
	default:
		return 0, "", ""
	}
}

func feedChannelAccessHash(ctx context.Context, hasher updates.ChannelAccessHasher, accountID int64, elem dialogs.Elem) {
	if hasher == nil {
		return
	}
	switch p := elem.Peer.(type) {
	case *tg.InputPeerChannel:
		if ch, ok := elem.Entities.Channel(p.ChannelID); ok {
			if hash, ok := ch.GetAccessHash(); ok {
				_ = hasher.SetChannelAccessHash(ctx, accountID, ch.ID, hash)
			}
		}
	}
}

func (l *Listener) syncDialogs(ctx context.Context, api *tg.Client, rt Runtime, hasher updates.ChannelAccessHasher, accountID int64) error {
	seen := make(map[int64]struct{})
	batch := make([]*workerspb.MonitoredChat, 0, dialogsBatchSize)
	var totalSynced int32

	flush := func() error {
		if len(batch) == 0 {
			return nil
		}
		synced, err := l.core.SyncChats(ctx, rt.WorkerID, batch)
		if err != nil {
			return err
		}
		totalSynced += synced
		batch = batch[:0]
		return nil
	}

	builder := dialogs.NewQueryBuilder(api).GetDialogs().BatchSize(dialogsBatchSize)
	err := builder.ForEach(ctx, func(ctx context.Context, elem dialogs.Elem) error {
		if elem.Deleted() {
			return nil
		}

		feedChannelAccessHash(ctx, hasher, accountID, elem)

		id, title, typ := chatFromElem(elem)
		if id == 0 {
			return nil
		}
		if _, ok := seen[id]; ok {
			return nil
		}
		seen[id] = struct{}{}
		rt.ChatTitles[id] = title
		batch = append(batch, &workerspb.MonitoredChat{
			WorkerId: rt.WorkerID,
			ChatId:   id,
			Title:    title,
			Type:     typ,
			IsActive: false,
		})

		if len(batch) >= dialogsBatchSize {
			return flush()
		}
		return nil
	})
	if err != nil {
		return err
	}
	if err := flush(); err != nil {
		return err
	}

	if totalSynced > 0 {
		log.Printf("worker %d: synced %d chats", rt.WorkerID, totalSynced)
	}
	return nil
}
