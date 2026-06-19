package manager

import (
	"context"
	"log"
	"os"
	"sync"
	"time"

	workerspb "github.com/sellbot/worker-engine/internal/gen/workers"
	"github.com/sellbot/worker-engine/internal/config"
	"github.com/sellbot/worker-engine/internal/core"
	"github.com/sellbot/worker-engine/internal/crypto"
	"github.com/sellbot/worker-engine/internal/listener"
	"github.com/sellbot/worker-engine/internal/publisher"
)

const workerPollInterval = 30 * time.Second

type Manager struct {
	cfg  config.Config
	core *core.Client
	nats *publisher.NATS

	mu      sync.Mutex
	running map[int64]context.CancelFunc
	syncCh  map[int64]chan struct{}
}

func New(cfg config.Config, coreClient *core.Client, nats *publisher.NATS) *Manager {
	return &Manager{
		cfg:     cfg,
		core:    coreClient,
		nats:    nats,
		running: map[int64]context.CancelFunc{},
		syncCh:  map[int64]chan struct{}{},
	}
}

func (m *Manager) Start(ctx context.Context) error {
	go m.listenSyncRequests(ctx)
	m.syncWorkers(ctx)

	ticker := time.NewTicker(workerPollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			m.stopAll()
			return nil
		case <-ticker.C:
			m.syncWorkers(ctx)
		}
	}
}

func (m *Manager) syncWorkers(ctx context.Context) {
	workers, err := m.core.GetActiveWorkers(ctx)
	if err != nil {
		log.Printf("GetActiveWorkers failed, keeping existing workers: %v", err)
		return
	}

	runtimes := m.buildRuntimes(ctx, workers)
	active := make(map[int64]bool, len(runtimes))
	for _, rt := range runtimes {
		active[rt.WorkerID] = true
		if !m.isRunning(rt.WorkerID) {
			m.startWorker(ctx, rt)
		}
	}
	m.stopExcept(active)
}

func (m *Manager) startWorker(parent context.Context, rt listener.Runtime) {
	syncCh := make(chan struct{}, 1)
	rt.SyncCh = syncCh

	m.mu.Lock()
	m.syncCh[rt.WorkerID] = syncCh
	m.mu.Unlock()

	workerCtx, cancel := context.WithCancel(parent)
	workerListener := listener.New(m.cfg, m.core, m.nats)

	m.mu.Lock()
	if old, ok := m.running[rt.WorkerID]; ok {
		old()
	}
	m.running[rt.WorkerID] = cancel
	m.mu.Unlock()

	log.Printf("starting worker %d (seller %d)", rt.WorkerID, rt.OwnerSellerID)
	go func() {
		defer func() {
			m.mu.Lock()
			delete(m.running, rt.WorkerID)
			delete(m.syncCh, rt.WorkerID)
			m.mu.Unlock()
		}()

		if err := workerListener.Run(workerCtx, rt); err != nil {
			log.Printf("worker %d stopped: %v", rt.WorkerID, err)
			if listener.IsAuthError(err) {
				if updateErr := m.core.UpdateWorkerStatus(context.Background(), rt.WorkerID, "auth_required"); updateErr != nil {
					log.Printf("worker %d: failed to update status: %v", rt.WorkerID, updateErr)
				} else {
					_ = m.nats.PublishWorkerStatus(publisher.WorkerStatusEvent{
						WorkerID:      rt.WorkerID,
						OwnerSellerID: rt.OwnerSellerID,
						Status:        "auth_required",
					})
				}
			}
		}
	}()
}

func (m *Manager) isRunning(workerID int64) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	_, ok := m.running[workerID]
	return ok
}

func (m *Manager) stopExcept(active map[int64]bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for id, cancel := range m.running {
		if !active[id] {
			log.Printf("stopping worker %d (no longer active)", id)
			cancel()
			delete(m.running, id)
			delete(m.syncCh, id)
		}
	}
}

func (m *Manager) stopAll() {
	m.mu.Lock()
	defer m.mu.Unlock()
	for id, cancel := range m.running {
		log.Printf("stopping worker %d (shutdown)", id)
		cancel()
		delete(m.running, id)
		delete(m.syncCh, id)
	}
}

func (m *Manager) listenSyncRequests(ctx context.Context) {
	if err := m.nats.SubscribeSyncChats(ctx, m.requestDialogSync); err != nil {
		log.Printf("sync chats subscription failed: %v", err)
	}
}

func (m *Manager) requestDialogSync(workerID int64) {
	m.mu.Lock()
	ch := m.syncCh[workerID]
	m.mu.Unlock()
	if ch == nil {
		return
	}
	select {
	case ch <- struct{}{}:
	default:
	}
}

func (m *Manager) buildRuntimes(ctx context.Context, workers []*workerspb.Worker) []listener.Runtime {
	if len(workers) > 0 {
		out := make([]listener.Runtime, 0, len(workers))
		for _, w := range workers {
			rt := listener.Runtime{
				WorkerID:      w.Id,
				OwnerSellerID: w.OwnerSellerId,
				ChatTitles:    map[int64]string{},
			}
			if session, err := m.loadWorkerSession(ctx, w.Id); err == nil {
				rt.SessionData = session
				out = append(out, rt)
			} else {
				log.Printf("worker %d: session load failed: %v", w.Id, err)
			}
		}
		if len(out) > 0 {
			return out
		}
	}

	if m.cfg.WorkerSessionString != "" || fileExists(m.cfg.WorkerSessionPath) {
		return []listener.Runtime{{
			WorkerID:      m.cfg.WorkerID,
			OwnerSellerID: m.cfg.OwnerSellerID,
			ChatTitles:    map[int64]string{},
		}}
	}
	return nil
}

func (m *Manager) loadWorkerSession(ctx context.Context, workerID int64) ([]byte, error) {
	enc, err := m.core.GetWorkerSession(ctx, workerID)
	if err != nil {
		return nil, err
	}
	if len(enc) == 0 {
		return nil, os.ErrNotExist
	}
	if m.cfg.SessionEncryptionKey == "" {
		return nil, os.ErrInvalid
	}
	return crypto.DecryptSession(m.cfg.SessionEncryptionKey, enc)
}

func fileExists(path string) bool {
	if path == "" {
		return false
	}
	_, err := os.Stat(path)
	return err == nil
}
