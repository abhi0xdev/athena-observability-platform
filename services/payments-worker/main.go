package main

import (
	"encoding/json"
	"math/rand"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"
	"os"
)

var logger = zerolog.New(os.Stdout).With().Timestamp().Logger()

var requestsTotal = prometheus.NewCounterVec(
	prometheus.CounterOpts{
		Name: "http_requests_total",
		Help: "Total HTTP requests",
	},
	[]string{"endpoint", "status"},
)

func healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "payments-worker",
	})
}

func payments(w http.ResponseWriter, r *http.Request) {

	time.Sleep(
		time.Duration(rand.Intn(2000)) *
			time.Millisecond,
	)

	logger.Info().
		Str("service", "payments-worker").
		Str("endpoint", "/payments").
		Msg("payment processed")

	w.Header().Set("Content-Type", "application/json")

	json.NewEncoder(w).Encode(map[string]string{
		"status": "payment-success",
	})
}

func main() {

	prometheus.MustRegister(requestsTotal)

	http.HandleFunc("/healthz", healthz)
	http.HandleFunc("/payments", payments)

	http.Handle(
		"/metrics",
		promhttp.Handler(),
	)

	logger.Info().
		Msg("payments-worker started on :8080")

	http.ListenAndServe(":8080", nil)
}