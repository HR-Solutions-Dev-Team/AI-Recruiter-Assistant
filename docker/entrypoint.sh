#!/usr/bin/env sh
set -e

CERT_DIR=${CERT_DIR:-/app/certs}
CERT_FILE=${SSL_CERT_FILE:-/app/certs/cert.pem}
KEY_FILE=${SSL_KEY_FILE:-/app/certs/key.pem}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-443}

mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -subj "/C=RU/ST=NA/L=NA/O=AIRecruiter/OU=IT/CN=localhost"
fi

exec uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --ssl-keyfile "$KEY_FILE" \
  --ssl-certfile "$CERT_FILE"
