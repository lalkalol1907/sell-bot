package login

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/gotd/td/telegram"
	"github.com/gotd/td/telegram/auth"
	"github.com/gotd/td/telegram/auth/qrlogin"
	"github.com/gotd/td/tg"

	"github.com/sellbot/worker-engine/internal/core"
	"github.com/sellbot/worker-engine/internal/crypto"
	"github.com/sellbot/worker-engine/internal/sessionstore"
)

const (
	StatusQRReady          = "qr_ready"
	StatusCodeSent         = "code_sent"
	StatusPasswordRequired = "password_required"
	StatusSuccess          = "success"
	StatusError            = "error"
)

const (
	modePhone = "phone"
	modeQR    = "qr"
)

var (
	ErrLoginNotFound = errors.New("login not found")
	ErrLoginExpired  = errors.New("login expired")
)

type Step struct {
	LoginID      string
	Status       string
	Message      string
	WorkerID     int64
	QrURL        string
	QrExpiresAt  int64
}

type Manager struct {
	apiID   int
	apiHash string
	encKey  string
	core    *core.Client
	mu      sync.Mutex
	pending map[string]*pendingLogin
	ttl     time.Duration
}

type pendingLogin struct {
	id            string
	ownerSellerID int64
	mode          string
	phone         string
	storage       *sessionstore.MemoryStorage
	createdAt     time.Time

	mu          sync.Mutex
	status      string
	message     string
	workerID    int64
	qrURL       string
	qrExpiresAt int64
	err         error
	done        chan struct{}
	statusCh    chan struct{}

	codeCh     chan string
	passwordCh chan string
}

func NewManager(apiID int, apiHash, encKey string, coreClient *core.Client) *Manager {
	m := &Manager{
		apiID:   apiID,
		apiHash: apiHash,
		encKey:  encKey,
		core:    coreClient,
		pending: map[string]*pendingLogin{},
		ttl:     10 * time.Minute,
	}
	go m.cleanupLoop()
	return m
}

func (m *Manager) validateConfig() error {
	if m.apiID == 0 || m.apiHash == "" {
		return fmt.Errorf("TG_API_ID and TG_API_HASH required")
	}
	if m.encKey == "" {
		return fmt.Errorf("SESSION_ENCRYPTION_KEY required")
	}
	if m.core == nil {
		return fmt.Errorf("core client unavailable")
	}
	return nil
}

func (m *Manager) StartLogin(ctx context.Context, ownerSellerID int64, phone string) (Step, error) {
	if err := m.validateConfig(); err != nil {
		return Step{}, err
	}

	id, err := newLoginID()
	if err != nil {
		return Step{}, err
	}

	pl := m.newPending(id, ownerSellerID, modePhone, phone)
	pl.setStatus(StatusCodeSent, "Отправляем код…")

	m.register(pl)
	go m.runPhoneLogin(context.Background(), pl)

	return m.waitInitial(ctx, pl, 45*time.Second, Step{LoginID: id, Status: StatusCodeSent, Message: "Код отправлен в Telegram"})
}

func (m *Manager) StartQRLogin(ctx context.Context, ownerSellerID int64) (Step, error) {
	if err := m.validateConfig(); err != nil {
		return Step{}, err
	}

	id, err := newLoginID()
	if err != nil {
		return Step{}, err
	}

	pl := m.newPending(id, ownerSellerID, modeQR, "")
	pl.setStatus(StatusQRReady, "Генерируем QR…")

	m.register(pl)
	go m.runQRLogin(context.Background(), pl)

	return m.waitInitial(ctx, pl, 30*time.Second, Step{LoginID: id, Status: StatusQRReady, Message: "Отсканируйте QR в Telegram"})
}

func (m *Manager) GetLoginStatus(loginID string) (Step, error) {
	pl, err := m.get(loginID)
	if err != nil {
		return Step{}, err
	}
	return pl.step(), nil
}

func (m *Manager) SubmitCode(ctx context.Context, loginID, code string) (Step, error) {
	pl, err := m.get(loginID)
	if err != nil {
		return Step{}, err
	}
	if pl.mode != modePhone {
		return Step{}, fmt.Errorf("login %s is not phone mode", loginID)
	}

	select {
	case pl.codeCh <- code:
	default:
		return Step{}, fmt.Errorf("code already submitted")
	}

	return m.waitStep(ctx, pl)
}

func (m *Manager) SubmitPassword(ctx context.Context, loginID, password string) (Step, error) {
	pl, err := m.get(loginID)
	if err != nil {
		return Step{}, err
	}
	if pl.mode != modePhone {
		return Step{}, fmt.Errorf("login %s is not phone mode", loginID)
	}

	select {
	case pl.passwordCh <- password:
	default:
		return Step{}, fmt.Errorf("password already submitted")
	}

	return m.waitStep(ctx, pl)
}

func (m *Manager) newPending(id string, ownerSellerID int64, mode, phone string) *pendingLogin {
	return &pendingLogin{
		id:            id,
		ownerSellerID: ownerSellerID,
		mode:          mode,
		phone:         phone,
		storage:       &sessionstore.MemoryStorage{},
		createdAt:     time.Now(),
		done:          make(chan struct{}),
		statusCh:      make(chan struct{}, 1),
		codeCh:        make(chan string, 1),
		passwordCh:    make(chan string, 1),
	}
}

func (m *Manager) register(pl *pendingLogin) {
	m.mu.Lock()
	m.pending[pl.id] = pl
	m.mu.Unlock()
}

func (m *Manager) waitInitial(ctx context.Context, pl *pendingLogin, timeout time.Duration, fallback Step) (Step, error) {
	select {
	case <-pl.done:
		return pl.step(), pl.err
	case <-pl.statusCh:
		return pl.step(), nil
	case <-time.After(timeout):
		step := pl.step()
		if step.Status == "" {
			return fallback, nil
		}
		return step, nil
	case <-ctx.Done():
		return Step{}, ctx.Err()
	}
}

func (m *Manager) waitStep(ctx context.Context, pl *pendingLogin) (Step, error) {
	select {
	case <-pl.done:
		step := pl.step()
		if pl.err != nil {
			return step, pl.err
		}
		return step, nil
	case <-pl.statusCh:
		return pl.step(), nil
	case <-time.After(60 * time.Second):
		return pl.step(), nil
	case <-ctx.Done():
		return Step{}, ctx.Err()
	}
}

func (m *Manager) get(loginID string) (*pendingLogin, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	pl, ok := m.pending[loginID]
	if !ok {
		return nil, ErrLoginNotFound
	}
	if time.Since(pl.createdAt) > m.ttl {
		delete(m.pending, loginID)
		return nil, ErrLoginExpired
	}
	return pl, nil
}

func (m *Manager) runPhoneLogin(ctx context.Context, pl *pendingLogin) {
	defer close(pl.done)

	err := m.authenticatePhone(ctx, pl)
	if err != nil {
		pl.setError(err)
		log.Printf("phone login %s failed: %v", pl.id, err)
	}
}

func (m *Manager) runQRLogin(ctx context.Context, pl *pendingLogin) {
	defer close(pl.done)

	dispatcher := tg.NewUpdateDispatcher()
	loggedIn := qrlogin.OnLoginToken(dispatcher)

	client := telegram.NewClient(m.apiID, m.apiHash, telegram.Options{
		SessionStorage: pl.storage,
		UpdateHandler:  dispatcher,
	})

	err := client.Run(ctx, func(ctx context.Context) error {
		show := func(ctx context.Context, token qrlogin.Token) error {
			pl.setQR(token.URL(), token.Expires().Unix())
			return nil
		}
		if _, err := client.QR().Auth(ctx, loggedIn, show); err != nil {
			return fmt.Errorf("qr auth: %w", err)
		}
		return m.finalizeSession(ctx, pl, client)
	})
	if err != nil {
		pl.setError(err)
		log.Printf("qr login %s failed: %v", pl.id, err)
	}
}

func (m *Manager) authenticatePhone(ctx context.Context, pl *pendingLogin) error {
	client := telegram.NewClient(m.apiID, m.apiHash, telegram.Options{
		SessionStorage: pl.storage,
	})

	return client.Run(ctx, func(ctx context.Context) error {
		authClient := client.Auth()

		sentCode, err := authClient.SendCode(ctx, pl.phone, auth.SendCodeOptions{})
		if err != nil {
			return fmt.Errorf("send code: %w", err)
		}
		pl.setStatus(StatusCodeSent, "Код отправлен в Telegram")

		code, err := pl.waitCode(ctx)
		if err != nil {
			return err
		}

		sent, ok := sentCode.(*tg.AuthSentCode)
		if !ok {
			return fmt.Errorf("unexpected sent code type %T", sentCode)
		}

		_, signInErr := authClient.SignIn(ctx, pl.phone, code, sent.PhoneCodeHash)
		if errors.Is(signInErr, auth.ErrPasswordAuthNeeded) {
			pl.setStatus(StatusPasswordRequired, "Введите пароль двухфакторной аутентификации")
			pass, err := pl.waitPassword(ctx)
			if err != nil {
				return err
			}
			if _, err := authClient.Password(ctx, pass); err != nil {
				return fmt.Errorf("2fa: %w", err)
			}
		} else if signInErr != nil {
			return fmt.Errorf("sign in: %w", signInErr)
		}

		return m.finalizeSession(ctx, pl, client)
	})
}

func (m *Manager) finalizeSession(ctx context.Context, pl *pendingLogin, client *telegram.Client) error {
	self, err := client.Self(ctx)
	if err != nil {
		return fmt.Errorf("self: %w", err)
	}

	sessionData := pl.storage.Data
	if len(sessionData) == 0 {
		return fmt.Errorf("empty session after login")
	}

	enc, err := crypto.EncryptSession(m.encKey, sessionData)
	if err != nil {
		return fmt.Errorf("encrypt session: %w", err)
	}

	phone := pl.phone
	if phone == "" {
		phone = self.Phone
	}

	worker, err := m.core.CreateWorker(ctx, pl.ownerSellerID, phone, self.ID, enc)
	if err != nil {
		return fmt.Errorf("create worker: %w", err)
	}

	username := self.Username
	if username != "" {
		username = "@" + username
	} else {
		username = fmt.Sprintf("id:%d", self.ID)
	}
	pl.setSuccess(worker.Id, fmt.Sprintf("Воркер #%d подключён (%s)", worker.Id, username))
	return nil
}

func (pl *pendingLogin) waitCode(ctx context.Context) (string, error) {
	select {
	case code := <-pl.codeCh:
		if code == "" {
			return "", fmt.Errorf("empty code")
		}
		return code, nil
	case <-ctx.Done():
		return "", ctx.Err()
	case <-time.After(pl.ttlRemaining()):
		return "", ErrLoginExpired
	}
}

func (pl *pendingLogin) waitPassword(ctx context.Context) (string, error) {
	select {
	case pass := <-pl.passwordCh:
		if pass == "" {
			return "", fmt.Errorf("empty password")
		}
		return pass, nil
	case <-ctx.Done():
		return "", ctx.Err()
	case <-time.After(pl.ttlRemaining()):
		return "", ErrLoginExpired
	}
}

func (pl *pendingLogin) ttlRemaining() time.Duration {
	remaining := 10*time.Minute - time.Since(pl.createdAt)
	if remaining < 0 {
		return 0
	}
	return remaining
}

func (pl *pendingLogin) setStatus(status, message string) {
	pl.mu.Lock()
	pl.status = status
	pl.message = message
	pl.mu.Unlock()
	pl.notifyStatus()
}

func (pl *pendingLogin) setQR(url string, expiresAt int64) {
	pl.mu.Lock()
	pl.qrURL = url
	pl.qrExpiresAt = expiresAt
	pl.status = StatusQRReady
	pl.message = "Отсканируйте QR в официальном Telegram"
	pl.mu.Unlock()
	pl.notifyStatus()
}

func (pl *pendingLogin) setSuccess(workerID int64, message string) {
	pl.mu.Lock()
	pl.status = StatusSuccess
	pl.message = message
	pl.workerID = workerID
	pl.mu.Unlock()
	pl.notifyStatus()
}

func (pl *pendingLogin) setError(err error) {
	pl.mu.Lock()
	pl.status = StatusError
	pl.message = err.Error()
	pl.err = err
	pl.mu.Unlock()
	pl.notifyStatus()
}

func (pl *pendingLogin) notifyStatus() {
	select {
	case pl.statusCh <- struct{}{}:
	default:
	}
}

func (pl *pendingLogin) step() Step {
	pl.mu.Lock()
	defer pl.mu.Unlock()
	return Step{
		LoginID:     pl.id,
		Status:      pl.status,
		Message:     pl.message,
		WorkerID:    pl.workerID,
		QrURL:       pl.qrURL,
		QrExpiresAt: pl.qrExpiresAt,
	}
}

func (m *Manager) cleanupLoop() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()
	for range ticker.C {
		now := time.Now()
		m.mu.Lock()
		for id, pl := range m.pending {
			if now.Sub(pl.createdAt) > m.ttl {
				delete(m.pending, id)
			}
		}
		m.mu.Unlock()
	}
}

func newLoginID() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	return hex.EncodeToString(b[:]), nil
}
