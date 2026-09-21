#!/bin/bash
# security/generate_certs.sh

mkdir -p certs
cd certs

# 1. Generate CA (Certificate Authority)
openssl req -new -x509 -days 365 -nodes -out ca.crt -keyout ca.key -subj "/CN=Pipeline Leak Risk Management CA"

# 2. Generate Server Certificate (for Mosquitto & FastAPI)
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# 3. Generate Client Certificate (for Jetson Edge)
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=JETSON-NODE-042"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365

echo "✅ Certificates generated in security/certs/"