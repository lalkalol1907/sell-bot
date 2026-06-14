package core

import (
	"context"
	"fmt"
	"time"

	workerspb "github.com/sellbot/worker-engine/internal/gen/workers"
	"github.com/sellbot/worker-engine/internal/grpcauth"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Client struct {
	conn           *grpc.ClientConn
	workers        workerspb.WorkersServiceClient
	internalSecret string
}

func NewClient(addr string, internalSecret string) (*Client, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	conn, err := grpc.DialContext(ctx, addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("dial core: %w", err)
	}
	return &Client{
		conn:           conn,
		workers:        workerspb.NewWorkersServiceClient(conn),
		internalSecret: internalSecret,
	}, nil
}

func (c *Client) Close() error {
	return c.conn.Close()
}

func (c *Client) GetActiveWorkers(ctx context.Context) ([]*workerspb.Worker, error) {
	resp, err := c.workers.GetActiveWorkers(ctx, &workerspb.GetActiveWorkersRequest{})
	if err != nil {
		return nil, err
	}
	return resp.Workers, nil
}

func (c *Client) SyncChats(ctx context.Context, workerID int64, chats []*workerspb.MonitoredChat) (int32, error) {
	resp, err := c.workers.SyncChats(ctx, &workerspb.SyncChatsRequest{
		WorkerId: workerID,
		Chats:    chats,
	})
	if err != nil {
		return 0, err
	}
	return resp.Synced, nil
}

func (c *Client) ListActiveChatIDs(ctx context.Context, workerID, ownerSellerID int64) (map[int64]bool, error) {
	resp, err := c.workers.ListChats(ctx, &workerspb.ListChatsRequest{
		WorkerId:      workerID,
		OwnerSellerId: ownerSellerID,
	})
	if err != nil {
		return nil, err
	}
	out := make(map[int64]bool)
	for _, ch := range resp.Chats {
		if ch.IsActive {
			out[ch.ChatId] = true
		}
	}
	return out, nil
}

func (c *Client) UpdateWorkerStatus(ctx context.Context, workerID int64, status string) error {
	_, err := c.workers.UpdateWorkerStatus(ctx, &workerspb.UpdateWorkerStatusRequest{
		Id:     workerID,
		Status: status,
	})
	return err
}

func (c *Client) CreateWorker(ctx context.Context, ownerSellerID int64, phone string, tgAccountID int64, sessionEnc []byte) (*workerspb.Worker, error) {
	return c.workers.CreateWorker(ctx, &workerspb.CreateWorkerRequest{
		OwnerSellerId: ownerSellerID,
		TgAccountId:   tgAccountID,
		Phone:         phone,
		SessionEnc:    sessionEnc,
	})
}

func (c *Client) GetWorkerSession(ctx context.Context, workerID int64) ([]byte, error) {
	ctx = grpcauth.OutgoingContext(ctx, c.internalSecret)
	resp, err := c.workers.GetWorkerSession(ctx, &workerspb.GetWorkerSessionRequest{
		WorkerId: workerID,
	})
	if err != nil {
		return nil, err
	}
	return resp.SessionEnc, nil
}
