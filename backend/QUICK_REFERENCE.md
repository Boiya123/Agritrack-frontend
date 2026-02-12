# Quick Reference: Using SupplyChainContractHelper

## Import

```python
from app.services.blockchain_service import (
    initialize_blockchain_service,
    SupplyChainContractHelper,
    BlockchainTransactionError
)
```

## Initialize

```python
blockchain_service = initialize_blockchain_service()
helper = SupplyChainContractHelper(blockchain_service)
```

## All Available Methods

### Product Functions

```python
await helper.create_product(product_id, name, description)
await helper.get_product(product_id)
```

### Batch Functions

```python
await helper.create_batch(
    batch_id, product_id, farmer_id, batch_number,
    quantity, start_date, expected_end_date, location,
    qr_code, notes
)
await helper.get_batch(batch_id)
```

### Lifecycle Events (Append-Only)

```python
await helper.record_lifecycle_event(
    event_id, batch_id, event_type, description,
    recorded_by, event_date, quantity_affected, metadata
)
await helper.get_batch_lifecycle_events(batch_id)
```

### Transport

```python
await helper.create_transport_manifest(
    transport_id, batch_id, from_party_id, to_party_id,
    vehicle_id, driver_name, departure_time,
    origin_location, destination_location,
    temperature_monitored, notes
)
await helper.get_transport(transport_id)
```

### Temperature (Auto-detects violations)

```python
await helper.add_temperature_log(
    log_id, transport_id, temperature, timestamp, location
)
await helper.get_transport_temperature_logs(transport_id)
```

### Processing

```python
await helper.record_processing(
    processing_id, batch_id, process_date, facility_name,
    slaughter_count, yield_kg, quality_score, notes
)
await helper.get_processing_record(processing_id)
```

### Certification (Regulator only)

```python
await helper.issue_certification(
    certification_id, processing_id, cert_type,
    issued_date, expiry_date, issuer_id, notes
)
await helper.get_certification(certification_id)
```

## Error Handling

```python
try:
    result = await helper.create_batch(...)
except BlockchainTransactionError as e:
    # Handle error - e.message contains specific guidance
    logger.error(f"Blockchain error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## In a FastAPI Route

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.routes.auth_routes import get_current_user
from app.database.session import get_db
from app.models.user_model import User
from app.services.blockchain_service import (
    initialize_blockchain_service,
    SupplyChainContractHelper,
    BlockchainTransactionError
)

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/create")
async def create_product(
    product_id: str,
    name: str,
    description: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new product (Regulator only)."""

    # Initialize blockchain service
    blockchain_service = initialize_blockchain_service()
    helper = SupplyChainContractHelper(blockchain_service)

    # Submit to blockchain
    try:
        blockchain_result = await helper.create_product(
            product_id=product_id,
            name=name,
            description=description,
        )
    except BlockchainTransactionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Also save to database
    # ... (your database logic here)

    return {
        "product_id": product_id,
        "blockchain_tx": blockchain_result
    }
```

## Testing Without Fabric

```python
from app.services.blockchain_service import (
    SupplyChainContractHelper,
    NoOpBlockchainService
)

# Use no-op service for testing
service = NoOpBlockchainService()
helper = SupplyChainContractHelper(service)

result = await helper.create_batch(...)  # Works without Fabric running
```

## Error Messages

| Scenario             | Error Message                                                 |
| -------------------- | ------------------------------------------------------------- |
| Function not found   | "Chaincode function 'X' not found in supplychain.go"          |
| Authorization denied | "Authorization failed for 'X'. Check caller MSP permissions." |
| Resource not found   | "Resource for 'X' does not exist. Verify the ID is correct."  |
| Connection failed    | "Failed to connect to Fabric peer: ..."                       |

## Configuration

Set in `.env`:

```env
FABRIC_CHANNEL=agritrack
FABRIC_CHAINCODE=supplychain
FABRIC_PEER_ENDPOINT=localhost:7051
FABRIC_MSP_ID=Org1MSP
FABRIC_IDENTITY=admin
FABRIC_TLS_CA_CERT=/path/to/ca.crt
FABRIC_IDENTITY_CERT=/path/to/client.crt
FABRIC_IDENTITY_KEY=/path/to/client.key
```

## Type Conversions

Integers and floats are automatically converted to strings:

```python
# These work fine - types are auto-converted
await helper.create_batch(
    batch_id="batch-001",
    product_id="prod-001",
    farmer_id="farmer-001",
    batch_number="BATCH-2026-001",
    quantity=1000,  # ← int, auto-converted to "1000"
    start_date="2026-01-01",
    expected_end_date="2026-02-01",
    location="Farm Alpha",
    qr_code="QR-001",
    notes="Healthy flock"
)

await helper.add_temperature_log(
    log_id="log-001",
    transport_id="transport-001",
    temperature=4.5,  # ← float, auto-converted to "4.5"
    timestamp="2026-02-04T10:00:00Z",
    location="In-transit"
)
```

## Complete Workflow Example

```python
async def complete_batch_workflow():
    blockchain_service = initialize_blockchain_service()
    helper = SupplyChainContractHelper(blockchain_service)

    # 1. Create product
    product = await helper.create_product(
        product_id="prod-001",
        name="Poultry",
        description="Chicken Production"
    )
    print(f"Product created: {product}")

    # 2. Create batch
    batch = await helper.create_batch(
        batch_id="batch-001",
        product_id="prod-001",
        farmer_id="farmer-001",
        batch_number="BATCH-2026-001",
        quantity=1000,
        start_date="2026-01-01",
        expected_end_date="2026-02-01",
        location="Farm Alpha",
        qr_code="QR-001",
        notes="Healthy flock"
    )
    print(f"Batch created: {batch}")

    # 3. Record lifecycle event
    event = await helper.record_lifecycle_event(
        event_id="event-001",
        batch_id="batch-001",
        event_type="VACCINATION",
        description="Avian Flu Vaccine",
        recorded_by="farmer-001",
        event_date="2026-01-15",
        quantity_affected=1000,
        metadata="Routine vaccination"
    )
    print(f"Event recorded: {event}")

    # 4. Query audit trail
    events = await helper.get_batch_lifecycle_events("batch-001")
    print(f"Audit trail: {events}")
```

---

**For more details**: See BLOCKCHAIN_SERVICE_UPDATE.md
**For integration plan**: See BLOCKCHAIN_INTEGRATION_CHECKLIST.md
**For testing**: See INTEGRATION_TESTING_GUIDE.md
