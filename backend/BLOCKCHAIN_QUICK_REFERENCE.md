# Quick Reference: Hyperledger Fabric Integration

## Files Modified/Created

| File                                          | Status         | Purpose                                 |
| --------------------------------------------- | -------------- | --------------------------------------- |
| `app/core/config.py`                          | ✅ Modified    | Added 8 Fabric configuration settings   |
| `app/services/blockchain_service.py`          | ✅ Implemented | Complete Fabric integration (397 lines) |
| `.env`                                        | ✅ Updated     | Added Fabric configuration template     |
| `docs/BLOCKCHAIN_SERVICE_INTEGRATION.md`      | ✅ Created     | Complete integration guide              |
| `docs/BLOCKCHAIN_ROUTE_EXAMPLES.md`           | ✅ Created     | Route usage examples                    |
| `docs/HYPERLEDGER_IMPLEMENTATION_COMPLETE.md` | ✅ Created     | Implementation summary                  |
| `FABRIC_INSTALLATION.md`                      | ✅ Created     | Installation instructions               |

## Configuration

```python
# In .env:
FABRIC_CHANNEL=agritrack
FABRIC_CHAINCODE=agritrack_cc
FABRIC_PEER_ENDPOINT=peer0.org1.example.com:7051
FABRIC_MSP_ID=Org1MSP
FABRIC_IDENTITY=admin
FABRIC_TLS_CA_CERT=/secrets/fabric/ca.crt
FABRIC_IDENTITY_CERT=/secrets/fabric/client.crt
FABRIC_IDENTITY_KEY=/secrets/fabric/client.key
```

## Installation

```bash
pip install fabric-gateway
```

## Usage in Routes

```python
from app.services.blockchain_service import initialize_blockchain_service, BlockchainServiceError

@router.post("/event")
async def create_event(data: EventData, db: Session = Depends(get_db)):
    # 1. Database operation (fast)
    event = Event(**data.dict())
    db.add(event)
    db.commit()

    # 2. Return API response
    response = {"id": event.id, "status": "created"}

    # 3. Blockchain write (non-blocking)
    try:
        blockchain = initialize_blockchain_service()
        await blockchain.submit_transaction("RecordEvent", str(event.id), "created")
    except BlockchainServiceError as e:
        logger.warning(f"Blockchain unavailable: {e}")

    return response
```

## Key Classes

### IBlockchainService (Abstract Interface)

```python
async def submit_transaction(function_name: str, *args: str) -> str
async def evaluate_transaction(function_name: str, *args: str) -> str
```

### FabricBlockchainService (Production Implementation)

- TLS/mTLS support
- Lazy connection initialization
- Comprehensive error handling
- Async transaction execution

### NoOpBlockchainService (Development Fallback)

- Logs operations
- Returns mock responses
- No network calls

## Exceptions

```python
BlockchainServiceError           # Base exception
├── BlockchainConnectionError    # Peer unavailable, TLS error
└── BlockchainTransactionError   # Chaincode execution failed
```

## Error Handling

```python
try:
    result = await blockchain.submit_transaction("Fn", "arg1", "arg2")
except BlockchainConnectionError:
    # Peer unavailable, retry or queue
    logger.warning("Will retry later")
except BlockchainTransactionError:
    # Chaincode error, investigate
    logger.error("Investigate chaincode error")
except BlockchainServiceError:
    # Generic error
    logger.error("Blockchain error")
```

## Testing

```python
from unittest.mock import AsyncMock, patch

mock_blockchain = AsyncMock()
mock_blockchain.submit_transaction = AsyncMock(return_value='{"ok":true}')

with patch(
    'app.services.blockchain_service.initialize_blockchain_service',
    return_value=mock_blockchain
):
    response = await my_endpoint()
    mock_blockchain.submit_transaction.assert_called_once()
```

## Security Checklist

- ✅ No private keys in code
- ✅ No certificates in code
- ✅ File paths from environment only
- ✅ TLS validation enforced
- ✅ mTLS (mutual auth) supported
- ✅ Secure credential loading
- ✅ No credentials in logs

## Deployment (Docker)

```yaml
services:
  api:
    environment:
      FABRIC_TLS_CA_CERT: /run/secrets/fabric_ca
      FABRIC_IDENTITY_CERT: /run/secrets/fabric_client_cert
      FABRIC_IDENTITY_KEY: /run/secrets/fabric_client_key
    secrets:
      - fabric_ca: { file: ./certs/ca.crt }
      - fabric_client_cert: { file: ./certs/client.crt }
      - fabric_client_key: { file: ./certs/client.key }
```

## Deployment (Kubernetes)

```yaml
env:
  - name: FABRIC_TLS_CA_CERT
    value: /etc/fabric-certs/ca.crt
volumeMounts:
  - name: fabric-certs
    mountPath: /etc/fabric-certs
volumes:
  - name: fabric-certs
    secret:
      secretName: fabric-certs
      defaultMode: 0400
```

## Architecture Principles

1. **Routes never import fabric-gateway** ← Always use service layer
2. **Non-blocking blockchain writes** ← API response fast, blockchain async
3. **Graceful degradation** ← API works if blockchain unavailable
4. **Lazy initialization** ← Connection on first use, no import-time side effects
5. **No embedded secrets** ← All credentials from environment

## Troubleshooting

| Error                          | Cause                         | Fix                                           |
| ------------------------------ | ----------------------------- | --------------------------------------------- |
| `TLS verification failed`      | Invalid CA cert               | Verify `FABRIC_TLS_CA_CERT` path and validity |
| `Connection refused`           | Peer unavailable              | Check `FABRIC_PEER_ENDPOINT` and firewall     |
| `Permission denied`            | Client cert invalid           | Re-enroll with Fabric CA                      |
| `Function not found`           | Wrong chaincode function name | Verify exact function name in chaincode       |
| `fabric-gateway not installed` | Missing dependency            | `pip install fabric-gateway`                  |

## Documentation Links

- **Full Integration Guide**: [docs/BLOCKCHAIN_SERVICE_INTEGRATION.md](docs/BLOCKCHAIN_SERVICE_INTEGRATION.md)
- **Route Examples**: [docs/BLOCKCHAIN_ROUTE_EXAMPLES.md](docs/BLOCKCHAIN_ROUTE_EXAMPLES.md)
- **Implementation Summary**: [docs/HYPERLEDGER_IMPLEMENTATION_COMPLETE.md](docs/HYPERLEDGER_IMPLEMENTATION_COMPLETE.md)
- **Installation**: [FABRIC_INSTALLATION.md](FABRIC_INSTALLATION.md)
