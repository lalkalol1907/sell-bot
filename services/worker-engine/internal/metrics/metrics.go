package metrics

import (
	"log"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	WorkersActive = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "worker_engine_workers_active",
		Help: "Number of running worker sessions",
	})
	MessagesCaptured = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "worker_engine_messages_captured_total",
		Help: "Messages captured and published to NATS",
	})
)

func init() {
	prometheus.MustRegister(WorkersActive, MessagesCaptured)
}

func StartServer(addr string) {
	if addr == "" {
		return
	}
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})
	go func() {
		log.Printf("metrics server on %s", addr)
		if err := http.ListenAndServe(addr, mux); err != nil {
			log.Printf("metrics server failed: %v", err)
		}
	}()
}
