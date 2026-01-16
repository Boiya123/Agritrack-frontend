# AgriTrack Blockchain Integration - Implementation Notes

## Consumer Transparency Vision

AgriTrack's blockchain integration enables **consumer trust through radical transparency**. When consumers scan a QR code on packaged poultry, they can see:

- ✅ Farmer certifications (and failed certifications)
- ✅ Disease outbreak history of the flock
- ✅ All regulatory violations on record
- ✅ Complete chain of custody from farm to consumer
- ✅ Processing and quality checks performed

**This builds trust because farmers cannot hide failures**—the blockchain record is permanent and public.

## Architecture Summary

### One-Way Data Flow

1. **Database** (source of truth) → **Message Queue** → **Blockchain** (immutable record)
2. No reverse sync from blockchain to database
3. Blockchain purely for transparency and audit trails

### Critical Events That Trigger Blockchain Writes

**In `lifecycle_routes.py`:**

- Disease outbreak reported
- Mortality rate exceeds threshold
- Health violations detected

**In `processing_routes.py`:**

- Quality check failures
- Processing facility violations
- Certification failures

**In `regulatory_routes.py`:**

- Regulator approvals/denials
- Health certificate issuance
- Compliance violations
- Export permit outcomes

### Event Structure

All blockchain events follow a consistent schema:

```python
{
  "type": "EVENT_TYPE",  # FARMER_COMPLIANCE, BATCH_EVENT, CUSTODY_CHANGE
  "farmer_id": "uuid",
  "batch_id": "uuid (if applicable)",
  "event": "ACTION_NAME",  # CERTIFICATION_FAILED, DISEASE_OUTBREAK
  "timestamp": "ISO 8601",
  "details": { "key": "value" },
  "severity": "LOW|MEDIUM|HIGH|CRITICAL"
}
```

## Implementation Sequence

### Step 1: Create Event Emission Service (No Hyperledger yet)

```python
# app/services/blockchain_service.py
class BlockchainEventEmitter:
    async def emit_event(self, event_data: dict):
        # For now, just logs to queue
        # Later: sends to message broker
        pass

async def emit_farmer_compliance_event(
    farmer_id: str,
    event: str,
    certification_type: str,
    reason: str,
    severity: str = "HIGH"
):
    # Called from regulatory_routes.py
    pass

async def emit_batch_event(
    batch_id: str,
    farmer_id: str,
    event: str,
    details: dict
):
    # Called from lifecycle_routes.py
    pass
```

### Step 2: Integrate Event Emission into Routes

In each route that handles compliance/violations, call the emitter:

```python
# In regulatory_routes.py - when certification fails
@router.post("/certifications/{cert_id}/fail")
async def fail_certification(
    cert_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certification = db.query(Certification).get(cert_id)
    certification.status = "FAILED"
    db.commit()

    # EMIT TO BLOCKCHAIN
    await emit_farmer_compliance_event(
        farmer_id=certification.farmer_id,
        event="CERTIFICATION_FAILED",
        certification_type=certification.type,
        reason=reason,
        severity="CRITICAL"
    )

    return certification
```

### Step 3: Add Message Queue Integration

When ready, upgrade `blockchain_service.py` to send events to RabbitMQ/Kafka.

### Step 4: Implement Consumer Query API

```python
# app/api/routes/blockchain_routes.py
@router.get("/farmers/{farmer_id}/history")
async def get_farmer_history(farmer_id: str):
    # Query blockchain for all events for this farmer
    # Return sorted by timestamp
    return farmer_events

@router.get("/batches/{batch_id}/certifications")
async def get_batch_certifications(batch_id: str):
    # Query blockchain for all certifications for this batch
    pass
```

## Configuration Files Ready

**`.env` now includes Hyperledger placeholders:**

```
HYPERLEDGER_NETWORK_CONFIG=/path/to/connection-profile.json
HYPERLEDGER_WALLET_PATH=/path/to/wallet
HYPERLEDGER_CHANNEL_NAME=agritrack
HYPERLEDGER_CHAINCODE_NAME=agritrack_cc
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
MESSAGE_QUEUE_TYPE=rabbitmq
```

## Testing the Integration

Once infrastructure is in place:

```python
# tests/integration/test_blockchain_events.py
def test_failed_certification_emits_blockchain_event():
    # Fail a certification
    # Assert event was queued for blockchain
    pass

def test_farmer_history_query():
    # Query farmer history from blockchain
    # Assert all events are returned
    pass
```

## Next Hands-On Steps

1. **Install dependencies**: Hyperledger Fabric SDK for Python, RabbitMQ client
2. **Create `blockchain_service.py`** with event emitter stubs
3. **Hook event emitters** into existing route handlers
4. **Test event emission** with print statements before connecting to actual blockchain
5. **Set up RabbitMQ** locally for development
6. **Connect to Hyperledger test network**
7. **Build consumer query API**

## Key Reminder

**The blockchain is for transparency, not for operational data.** All transactions happen in the database first. The blockchain records what happened—immutably and publicly.
