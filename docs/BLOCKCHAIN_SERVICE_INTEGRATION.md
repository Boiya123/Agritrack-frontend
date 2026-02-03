# Blockchain Service Integration Guide

## Overview

The blockchain service provides a clean abstraction layer for Hyperledger Fabric integration. Routes never import `fabric-gateway` directly—they call service functions instead.

## Configuration

### 1. Environment Variables

Set these in `.env` or inject via Docker Secrets / Kubernetes Secrets:

```env
# Required for blockchain to be active
FABRIC_CHANNEL=agritrack
FABRIC_CHAINCODE=agritrack_cc
FABRIC_PEER_ENDPOINT=peer0.org1.example.com:7051
FABRIC_MSP_ID=Org1MSP
FABRIC_IDENTITY=admin

# File paths to TLS credentials (never embed credentials in code)
FABRIC_TLS_CA_CERT=/secrets/fabric/ca.crt
FABRIC_IDENTITY_CERT=/secrets/fabric/client.crt
FABRIC_IDENTITY_KEY=/secrets/fabric/client.key
```

### 2. Certificate File Injection

In production, inject certificate files via:

**Docker Secrets:**

```bash
docker secret create fabric-ca-cert /path/to/ca.crt
docker service create \
  --secret fabric-ca-cert \
  --env FABRIC_TLS_CA_CERT=/run/secrets/fabric-ca-cert \
  ...
```

**Kubernetes Secrets:**

```bash
kubectl create secret generic fabric-certs \
  --from-file=ca.crt=./certs/ca.crt \
  --from-file=client.crt=./certs/client.crt \
  --from-file=client.key=./certs/client.key

# In deployment spec:
env:
  - name: FABRIC_TLS_CA_CERT
    value: /etc/fabric/ca.crt
volumeMounts:
  - name: fabric-certs
    mountPath: /etc/fabric
volumes:
  - name: fabric-certs
    secret:
      secretName: fabric-certs
```

## Usage in Routes

### Basic Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User
from app.services.blockchain_service import initialize_blockchain_service, BlockchainTransactionError

router = APIRouter(prefix="/example", tags=["example"])

@router.post("/record-event")
async def record_event(
    data: EventData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Your normal API logic (database operations)
    event = Event(**data.dict())
    db.add(event)
    db.commit()
    db.refresh(event)

    # 2. Optionally: record to blockchain (deferred, non-blocking)
    try:
        blockchain_service = initialize_blockchain_service()
        await blockchain_service.submit_transaction(
            "RecordFarmerComplianceEvent",
            str(event.farmer_id),
            "CERTIFICATION_FAILED",
            "Failed food safety audit"
        )
    except BlockchainTransactionError as e:
        # Log but don't fail the API response
        # In production, queue this for retry
        logger.warning(f"Blockchain write deferred: {e}")

    return event
```

### Transaction Types

**Submit Transaction (write operation):**

```python
blockchain = initialize_blockchain_service()
result = await blockchain.submit_transaction(
    "RecordComplianceEvent",           # chaincode function name
    "farmer-uuid-123",                  # arg 1
    "CERTIFICATION_FAILED",             # arg 2
    "Temperature audit violation"       # arg 3
)
```

**Evaluate Transaction (read operation):**

```python
blockchain = initialize_blockchain_service()
history = await blockchain.evaluate_transaction(
    "GetFarmerHistory",                # chaincode function name
    "farmer-uuid-123"                  # arg 1
)
farmer_events = json.loads(history)
```

## Error Handling

### Exception Types

```python
from app.services.blockchain_service import (
    BlockchainServiceError,        # Base exception
    BlockchainConnectionError,     # Can't connect to peer
    BlockchainTransactionError,    # Chaincode execution failed
)

try:
    await blockchain.submit_transaction(...)
except BlockchainConnectionError as e:
    # Peer unavailable, TLS cert invalid, network error
    # Typically should retry or queue
    logger.error(f"Blockchain unavailable: {e}")
except BlockchainTransactionError as e:
    # Chaincode error (wrong function, bad args, chaincode logic error)
    # Usually a programming error, needs investigation
    logger.error(f"Chaincode failed: {e}")
except BlockchainServiceError as e:
    # Generic blockchain error
    logger.error(f"Blockchain error: {e}")
```

## Behavior When Not Configured

If Hyperledger configuration is incomplete (missing environment variables):

- Service falls back to `NoOpBlockchainService`
- All transaction calls log but don't fail
- API remains fully functional
- Useful for development and testing

Example log output:

```
[NOOP] Would submit transaction: RecordComplianceEvent with args: ('farmer-123', 'FAILED', 'reason')
```

## Best Practices

### 1. Non-Blocking Writes

Don't block API responses waiting for blockchain:

```python
@router.post("/create-batch")
async def create_batch(
    data: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # API transaction first (fast response)
    batch = Batch(**data.dict(), farmer_id=current_user.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Blockchain write second (can fail without breaking API)
    try:
        blockchain = initialize_blockchain_service()
        # Fire and forget (don't await in production API response path)
        # In real code, use message queue for this
        await blockchain.submit_transaction(
            "RecordBatchCreated",
            str(batch.id),
            str(batch.farmer_id),
            str(batch.product_id)
        )
    except Exception as e:
        # Queue for retry or log for manual investigation
        logger.warning(f"Blockchain write failed: {e}")

    return batch
```

### 2. Chaincode Function Names

Always pass exact chaincode function name:

```python
# GOOD: Matches function definition in chaincode
await blockchain.submit_transaction("RecordFarmerComplianceEvent", ...)

# BAD: Wrong case or naming
await blockchain.submit_transaction("recordFarmerComplianceEvent", ...)
```

### 3. String Arguments Only

All chaincode arguments must be strings:

```python
# GOOD: Convert to strings
import json
await blockchain.submit_transaction(
    "RecordBatchEvent",
    str(batch_id),
    json.dumps({"mortality_rate": 0.05, "count": 25})
)

# BAD: Non-string arguments fail
await blockchain.submit_transaction(
    "RecordBatchEvent",
    batch_id,          # UUID object, not string
    25                 # int, not string
)
```

### 4. Testing

Mock the blockchain service for unit tests:

```python
from unittest.mock import AsyncMock, patch

# In test:
mock_blockchain = AsyncMock()
mock_blockchain.submit_transaction = AsyncMock(return_value='{"status":"ok"}')

with patch(
    'app.services.blockchain_service.initialize_blockchain_service',
    return_value=mock_blockchain
):
    response = await my_endpoint_handler()
    mock_blockchain.submit_transaction.assert_called_once()
```

## Production Deployment

### Docker Compose Example

```yaml
services:
  agritrack-api:
    build: .
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/agritrack
      FABRIC_CHANNEL: agritrack
      FABRIC_CHAINCODE: agritrack_cc
      FABRIC_PEER_ENDPOINT: fabric-peer:7051
      FABRIC_MSP_ID: Org1MSP
      FABRIC_IDENTITY: admin
      FABRIC_TLS_CA_CERT: /run/secrets/fabric_ca
      FABRIC_IDENTITY_CERT: /run/secrets/fabric_client_cert
      FABRIC_IDENTITY_KEY: /run/secrets/fabric_client_key
    secrets:
      - fabric_ca
      - fabric_client_cert
      - fabric_client_key

secrets:
  fabric_ca:
    file: ./certs/ca.crt
  fabric_client_cert:
    file: ./certs/client.crt
  fabric_client_key:
    file: ./certs/client.key
```

### Kubernetes Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fabric-certs
type: Opaque
data:
  ca.crt: <base64-encoded-ca-cert>
  client.crt: <base64-encoded-client-cert>
  client.key: <base64-encoded-client-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agritrack-api
spec:
  template:
    spec:
      containers:
        - name: api
          image: agritrack:latest
          env:
            - name: FABRIC_CHANNEL
              value: "agritrack"
            - name: FABRIC_CHAINCODE
              value: "agritrack_cc"
            - name: FABRIC_PEER_ENDPOINT
              value: "fabric-peer.fabric-network:7051"
            - name: FABRIC_MSP_ID
              value: "Org1MSP"
            - name: FABRIC_IDENTITY
              value: "admin"
            - name: FABRIC_TLS_CA_CERT
              value: "/etc/fabric-certs/ca.crt"
            - name: FABRIC_IDENTITY_CERT
              value: "/etc/fabric-certs/client.crt"
            - name: FABRIC_IDENTITY_KEY
              value: "/etc/fabric-certs/client.key"
          volumeMounts:
            - name: fabric-certs
              mountPath: /etc/fabric-certs
              readOnly: true
      volumes:
        - name: fabric-certs
          secret:
            secretName: fabric-certs
            defaultMode: 0400
```

## Troubleshooting

### TLS Certificate Errors

```
BlockchainConnectionError: Failed to connect to Fabric peer: ... certificate verify failed
```

**Causes:**

- CA certificate path invalid (`FABRIC_TLS_CA_CERT`)
- CA certificate expired or self-signed (not trusted)
- Wrong peer endpoint

**Fix:**

1. Verify file paths exist: `test -f $FABRIC_TLS_CA_CERT`
2. Check certificate validity: `openssl x509 -in $FABRIC_TLS_CA_CERT -text -noout`
3. Verify peer endpoint is correct

### Connection Timeout

```
BlockchainConnectionError: Failed to connect to Fabric peer: ... deadline exceeded
```

**Causes:**

- Peer not running
- Wrong peer endpoint
- Firewall blocking port 7051

**Fix:**

1. Verify peer is running: `telnet peer-host 7051`
2. Check `FABRIC_PEER_ENDPOINT` format (should be `host:port`)
3. Check firewall rules

### Invalid Identity

```
BlockchainConnectionError: Failed to connect to Fabric peer: ... permission denied
```

**Causes:**

- `FABRIC_IDENTITY_CERT` or `FABRIC_IDENTITY_KEY` invalid
- Client certificate doesn't match Fabric enrollment

**Fix:**

1. Re-enroll client with Fabric CA
2. Verify certificates match identity in Fabric network

## Future Enhancements

- [ ] Message queue integration (RabbitMQ/Kafka) for async blockchain writes
- [ ] Automatic retry with exponential backoff
- [ ] Blockchain write batching for performance
- [ ] Consumer-facing transparency endpoints
- [ ] Real-time blockchain event subscriptions
