package gapstore

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"sync"

	"github.com/go-faster/errors"
	"github.com/gotd/td/telegram/updates"
)

var (
	_ updates.StateStorage      = (*Store)(nil)
	_ updates.ChannelAccessHasher = (*Store)(nil)
)

type persisted struct {
	HasState     bool             `json:"has_state"`
	State        updates.State    `json:"state"`
	Channels     map[string]int   `json:"channels"`
	AccessHashes map[string]int64 `json:"access_hashes"`
}

// Store persists gotd updates state and channel access hashes on disk.
type Store struct {
	path string
	mu   sync.Mutex
	data persisted
}

// Open loads or creates a store file for one worker.
func Open(dir string, workerID int64) (*Store, error) {
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return nil, fmt.Errorf("mkdir updates state dir: %w", err)
	}

	path := filepath.Join(dir, fmt.Sprintf("worker-%d.json", workerID))
	s := &Store{
		path: path,
		data: persisted{
			Channels:     map[string]int{},
			AccessHashes: map[string]int64{},
		},
	}

	raw, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return s, nil
	}
	if err != nil {
		return nil, fmt.Errorf("read updates state: %w", err)
	}
	if err := json.Unmarshal(raw, &s.data); err != nil {
		return nil, fmt.Errorf("decode updates state: %w", err)
	}
	if s.data.Channels == nil {
		s.data.Channels = map[string]int{}
	}
	if s.data.AccessHashes == nil {
		s.data.AccessHashes = map[string]int64{}
	}
	return s, nil
}

func (s *Store) GetState(_ context.Context, _ int64) (updates.State, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return updates.State{}, false, nil
	}
	return s.data.State, true, nil
}

func (s *Store) SetState(_ context.Context, _ int64, state updates.State) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data.HasState = true
	s.data.State = state
	s.data.Channels = map[string]int{}
	return s.persistLocked()
}

func (s *Store) SetPts(_ context.Context, _ int64, pts int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("internalState not found")
	}
	s.data.State.Pts = pts
	return s.persistLocked()
}

func (s *Store) SetQts(_ context.Context, _ int64, qts int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("internalState not found")
	}
	s.data.State.Qts = qts
	return s.persistLocked()
}

func (s *Store) SetDate(_ context.Context, _ int64, date int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("internalState not found")
	}
	s.data.State.Date = date
	return s.persistLocked()
}

func (s *Store) SetSeq(_ context.Context, _ int64, seq int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("internalState not found")
	}
	s.data.State.Seq = seq
	return s.persistLocked()
}

func (s *Store) SetDateSeq(_ context.Context, _ int64, date, seq int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("internalState not found")
	}
	s.data.State.Date = date
	s.data.State.Seq = seq
	return s.persistLocked()
}

func (s *Store) SetChannelPts(_ context.Context, _, channelID int64, pts int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("user internalState does not exist")
	}
	s.data.Channels[channelKey(channelID)] = pts
	return s.persistLocked()
}

func (s *Store) GetChannelPts(_ context.Context, _, channelID int64) (int, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return 0, false, nil
	}
	pts, ok := s.data.Channels[channelKey(channelID)]
	return pts, ok, nil
}

func (s *Store) ForEachChannels(_ context.Context, _ int64, f func(context.Context, int64, int) error) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if !s.data.HasState {
		return errors.New("channels map does not exist")
	}
	for key, pts := range s.data.Channels {
		id, err := strconv.ParseInt(key, 10, 64)
		if err != nil {
			continue
		}
		if err := f(context.Background(), id, pts); err != nil {
			return err
		}
	}
	return nil
}

func (s *Store) SetChannelAccessHash(_ context.Context, _, channelID, accessHash int64) error {
	if accessHash == 0 {
		return nil
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data.AccessHashes[channelKey(channelID)] = accessHash
	return s.persistLocked()
}

func (s *Store) GetChannelAccessHash(_ context.Context, _, channelID int64) (int64, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	hash, ok := s.data.AccessHashes[channelKey(channelID)]
	return hash, ok, nil
}

func channelKey(channelID int64) string {
	return strconv.FormatInt(channelID, 10)
}

func (s *Store) persistLocked() error {
	raw, err := json.MarshalIndent(s.data, "", "  ")
	if err != nil {
		return err
	}
	tmp := s.path + ".tmp"
	if err := os.WriteFile(tmp, raw, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, s.path)
}
