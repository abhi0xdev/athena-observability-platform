const express = require("express");
const axios = require("axios");
const client = require("prom-client");

const app = express();

app.use(express.json());

// --------------------------
// Prometheus Metrics
// --------------------------

client.collectDefaultMetrics();

const httpRequestsTotal = new client.Counter({
  name: "http_requests_total",
  help: "Total HTTP requests",
  labelNames: ["endpoint", "status"],
});

const httpRequestDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "HTTP request duration",
  labelNames: ["endpoint"],
  buckets: [0.1, 0.25, 0.5, 1, 2, 5],
});

// --------------------------
// Middleware
// --------------------------

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer({
    endpoint: req.path,
  });

  res.on("finish", () => {
    httpRequestsTotal.inc({
      endpoint: req.path,
      status: res.statusCode,
    });

    end();
  });

  next();
});

// --------------------------
// Routes
// --------------------------

app.get("/healthz", (req, res) => {
  res.json({
    status: "ok",
    service: "orders-service",
  });
});

app.post("/orders", async (req, res) => {
  try {
    const response = await axios.post(
      process.env.CHECKOUT_API_URL ||
        "http://checkout-api:8000/checkout"
    );

    res.status(200).json({
      status: "order-created",
      checkout: response.data,
    });
  } catch (error) {
    res.status(500).json({
      status: "failed",
      error: error.message,
    });
  }
});

app.get("/metrics", async (req, res) => {
  res.set(
    "Content-Type",
    client.register.contentType
  );

  res.end(
    await client.register.metrics()
  );
});

// --------------------------
// Start Server
// --------------------------

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`orders-service listening on ${PORT}`);
});