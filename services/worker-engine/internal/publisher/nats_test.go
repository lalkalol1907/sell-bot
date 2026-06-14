package publisher_test

import (
	"testing"

	"github.com/sellbot/worker-engine/internal/publisher"
)

func TestParseIDsDefaults(t *testing.T) {
	s, w, c, a, err := publisher.ParseIDs("", "", "", "", 1, 2, 3, 4)
	if err != nil {
		t.Fatal(err)
	}
	if s != 1 || w != 2 || c != 3 || a != 4 {
		t.Fatalf("defaults mismatch: %d %d %d %d", s, w, c, a)
	}
}

func TestParseIDsExplicit(t *testing.T) {
    s, w, c, a, err := publisher.ParseIDs("10", "20", "30", "40", 0, 0, 0, 0)
	if err != nil {
		t.Fatal(err)
	}
	if s != 10 || w != 20 || c != 30 || a != 40 {
		t.Fatalf("parsed mismatch: %d %d %d %d", s, w, c, a)
	}
}

func TestParseIDsInvalid(t *testing.T) {
	_, _, _, _, err := publisher.ParseIDs("bad", "", "", "", 0, 0, 0, 0)
	if err == nil {
		t.Fatal("expected parse error")
	}
}

func TestCapturedMessageJSON(t *testing.T) {
	msg := publisher.CapturedMessage{
		SellerID:       1,
		WorkerID:       2,
		ChatID:         -100123,
		MessageID:      99,
		AuthorID:       555,
		AuthorUsername: "buyer",
		ChatTitle:      "Test",
		RawText:        "куплю айфон",
	}
	if msg.SellerID != 1 || msg.RawText != "куплю айфон" {
		t.Fatal("struct fields mismatch")
	}
}
