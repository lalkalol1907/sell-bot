package crypto_test

import (
	"encoding/base64"
	"testing"

	"github.com/sellbot/worker-engine/internal/crypto"
)

func validKey() string {
	key := make([]byte, 32)
	for i := range key {
		key[i] = byte(i)
	}
	return base64.StdEncoding.EncodeToString(key)
}

func TestEncryptDecryptRoundTrip(t *testing.T) {
	plain := []byte(`{"version":1,"data":"session"}`)
	enc, err := crypto.EncryptSession(validKey(), plain)
	if err != nil {
		t.Fatalf("encrypt: %v", err)
	}
	got, err := crypto.DecryptSession(validKey(), enc)
	if err != nil {
		t.Fatalf("decrypt: %v", err)
	}
	if string(got) != string(plain) {
		t.Fatalf("round-trip mismatch: %q != %q", got, plain)
	}
}

func TestEncryptInvalidKeyLength(t *testing.T) {
	_, err := crypto.EncryptSession(base64.StdEncoding.EncodeToString([]byte("short")), []byte("x"))
	if err == nil {
		t.Fatal("expected error for short key")
	}
}

func TestDecryptEmptyCiphertext(t *testing.T) {
	_, err := crypto.DecryptSession(validKey(), nil)
	if err == nil {
		t.Fatal("expected error for empty ciphertext")
	}
}

func TestDecryptTamperedCiphertext(t *testing.T) {
	enc, err := crypto.EncryptSession(validKey(), []byte("secret"))
	if err != nil {
		t.Fatal(err)
	}
	enc[len(enc)-1] ^= 0xff
	_, err = crypto.DecryptSession(validKey(), enc)
	if err == nil {
		t.Fatal("expected error for tampered ciphertext")
	}
}

func TestDecryptWrongKey(t *testing.T) {
	enc, err := crypto.EncryptSession(validKey(), []byte("secret"))
	if err != nil {
		t.Fatal(err)
	}
	otherKey := make([]byte, 32)
	for i := range otherKey {
		otherKey[i] = byte(255 - i)
	}
	_, err = crypto.DecryptSession(base64.StdEncoding.EncodeToString(otherKey), enc)
	if err == nil {
		t.Fatal("expected error for wrong key")
	}
}
