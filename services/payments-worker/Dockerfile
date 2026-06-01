FROM golang:1.25 AS builder

WORKDIR /app

COPY . .

RUN go mod tidy

RUN CGO_ENABLED=0 GOOS=linux go build -o payments-worker

FROM alpine:3.21

WORKDIR /app

COPY --from=builder /app/payments-worker .

EXPOSE 8080

CMD ["./payments-worker"]