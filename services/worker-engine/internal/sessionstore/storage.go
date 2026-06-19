package sessionstore

import (
	"context"
	"os"

	"github.com/gotd/td/session"
)

// MemoryStorage stores gotd session bytes in memory.
type MemoryStorage struct {
	Data []byte
}

func (s *MemoryStorage) LoadSession(_ context.Context) ([]byte, error) {
	if len(s.Data) == 0 {
		return nil, session.ErrNotFound
	}
	return s.Data, nil
}

func (s *MemoryStorage) StoreSession(_ context.Context, data []byte) error {
	s.Data = append([]byte(nil), data...)
	return nil
}

// FileStorage wraps gotd session file path.
type FileStorage struct {
	Path string
}

func (s *FileStorage) LoadSession(_ context.Context) ([]byte, error) {
	data, err := os.ReadFile(s.Path)
	if os.IsNotExist(err) {
		return nil, session.ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	return data, nil
}

func (s *FileStorage) StoreSession(_ context.Context, data []byte) error {
	return os.WriteFile(s.Path, data, 0o600)
}
