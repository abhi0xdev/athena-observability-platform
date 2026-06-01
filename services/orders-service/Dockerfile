# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install --omit=dev

COPY . .

# Runtime stage
FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app .

EXPOSE 3000

ENV PORT=3000
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

CMD ["node", "-r", "./otel.js", "app.js"]