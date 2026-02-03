# AgriTrack Hyperledger Fabric Chaincode Architecture

## Overview

The AgriTrack chaincode implements a **deterministic, append-only supply chain ledger** for agricultural traceability. It stores immutable records of:

- Product definitions
- Batch lifecycle (creation → production → completion)
- Lifecycle events (append-only audit trail)
- Transport logistics with cold chain monitoring
- Processing facility records
- Regulatory certifications and approvals

**Design Principle**: The database is the source of truth for operational data; the blockchain is the source of truth for **audit, compliance, and consumer transparency**.

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  FABRIC CLIENT APPLICATIONS                     │
│  (AgriTrack FastAPI, Mobile Apps, Regulators)   │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Hyperledger     │
        │  Fabric Network  │
        │  (Peers/Orderer) │
        └────────┬────────┘
                 │
┌────────────────▼────────────────────────────────┐
│  SUPPLY CHAIN CONTRACT (Go Chaincode)           │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Authorization Layer (MSP-Based)         │   │
│  │  - FarmOrgMSP (Farmers)                  │   │
│  │  - RegulatorOrgMSP (Regulators)          │   │
│  │  - AdminOrgMSP (Full Access)             │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Validation Layer                        │   │
│  │  - Business rule enforcement             │   │
│  │  - Data type validation                  │   │
│  │  - Referential integrity                 │   │
│  │  - Status machine enforcement            │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  State Management (8 Asset Types)        │   │
│  │  - Product definitions                   │   │
│  │  - Batch records (mutable)               │   │
│  │  - Lifecycle events (append-only)        │   │
│  │  - Transport manifests                   │   │
│  │  - Temperature logs                      │   │
│  │  - Processing records                    │   │
│  │  - Certifications                        │   │
│  │  - Regulatory approvals                  │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Event Emission (Fabric Events)          │   │
│  │  - BatchCreated                          │   │
│  │  - LifecycleEventRecorded                │   │
│  │  - TransportCreated                      │   │
│  │  - TemperatureViolationDetected          │   │
│  │  - ProcessingRecorded                    │   │
│  │  - CertificationUpdated                  │   │
│  │  - RegulatoryRecordUpdated               │   │
│  └──────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────┘
                 │
         ┌───────▼────────┐
         │  CouchDB       │
         │  World State   │
         │  (Ledger)      │
         └────────────────┘
```

## Data Model Design

### Asset Hierarchy

```
ProductAsset (reference data)
    ↓
BatchAsset (aggregate root)
    ├→ LifecycleEventAsset* (append-only timeline)
    ├→ TransportAsset (mutable during transit)
    │   └→ TemperatureLogAsset* (append-only readings)
    ├→ ProcessingAsset (final output)
    │   └→ CertificationAsset (regulatory approval)
    └→ RegulatoryAsset (compliance record)

* Append-only: can only be created, never updated
```

### State Key Design

Ledger keys are **deterministic** using business identifiers:

```
Product:       [ProductID]
Batch:         [BatchID]
LifecycleEvent:[EventID]
Transport:     [TransportID]
TempLog:       [LogID]
Processing:    [ProcessingID]
Certification: [CertificationID]
Regulatory:    [RegulatoryID]
```

**No sequential IDs or timestamps in keys** → ensures deterministic key generation across replicas.

## Authorization Model

Access control uses **Fabric MSP (Membership Service Provider)** identity:

```yaml
FarmOrgMSP:
  Can:
    - CreateBatch (only own batches via farmer_id validation)
    - RecordLifecycleEvent (only own batches)
    - CreateTransportManifest
    - UpdateTransportStatus
    - AddTemperatureLog
    - RecordProcessing
  Cannot:
    - Certify products (Regulator only)
    - Create regulatory records (Regulator only)

RegulatorOrgMSP:
  Can:
    - Create/Deactivate products
    - Issue certifications
    - Update certification status
    - Create regulatory records
    - Update regulatory status
    - Query all assets
  Cannot:
    - Modify farmer batches

AdminOrgMSP:
  Can: Everything
```

## Determinism Guarantees

**Critical**: Chaincode must be 100% deterministic for blockchain consensus.

### ✅ What We Do

- Use `ctx.GetStub().GetTxTimestamp()` (Fabric-provided, same across all peers)
- Deterministic JSON serialization for all assets
- Validation-based decisions (no randomness)
- UUIDs from function arguments (not generated in chaincode)

### ❌ What We Avoid

- `time.Now()` ← Uses system clock (non-deterministic)
- `rand.*` ← Generates random values
- External API calls ← Network timing non-deterministic
- File I/O ← Filesystem state non-deterministic
- Go maps iteration ← Iteration order non-deterministic

## Validation Strategy

### Layer 1: Input Validation

```go
// All function inputs validated before state access
ValidateNonEmptyString(id, "ID")
ValidatePositiveInt(quantity, "quantity")
ValidatePositiveFloat(temperature, "temperature")
```

### Layer 2: Referential Integrity

```go
// Before creating lifecycle event: batch must exist
batch, err := s.GetBatch(ctx, batchID)
if err != nil {
    return nil, fmt.Errorf("batch does not exist")
}
```

### Layer 3: Business Rules

```go
// Check batch_number uniqueness (composite key query)
query := fmt.Sprintf(`{"selector":{"docType":"BatchAsset","batch_number":"%s"}}`, batchNumber)
```

### Layer 4: State Machine Validation

```go
// Status transitions must follow defined paths
if err := s.ValidateStatusTransition(current, next); err != nil {
    return nil, err  // Invalid transition
}
```

## Immutability Patterns

### Append-Only Assets

Lifecycle events **cannot be updated, only created**:

```go
// ✅ Correct: New event with unique ID
RecordLifecycleEvent(eventID, batchID, ...)

// ❌ Wrong: Attempt to update event
UpdateLifecycleEvent(eventID, ...)  // Not implemented
```

**Audit Trail Benefit**: Complete historical record. If a vaccination wasn't recorded, it's permanently missing from blockchain.

### Mutable Assets

Batch status transitions follow valid state paths:

```
CREATED → IN_PROGRESS → COMPLETED (terminal)
       ↓
       FAILED → IN_PROGRESS (retry)

CREATED → CANCELLED (terminal)
```

## Event Emission

Chaincode emits **Fabric events** for critical state changes:

```go
// Example: Temperature violation detected
eventPayload := map[string]interface{}{
    "transport_id": transportID,
    "temperature":  5.2,
    "threshold":    "2.0-8.0°C",
}
ctx.GetStub().SetEvent("TemperatureViolationDetected", marshal(eventPayload))
```

**Use Cases**:

- Alert systems (temperature violations)
- Audit logging (certifications approved/rejected)
- Real-time dashboards (batch status updates)

## Query Patterns

### CouchDB JSON Query (Rich Query)

```go
query := fmt.Sprintf(
    `{"selector":{"docType":"BatchAsset","farmer_id":"%s"}}`,
    farmerID,
)
iterator, _ := ctx.GetStub().GetQueryResultsForQueryString(query)
```

**Supported Queries**:

- `GetBatchesByFarmer(farmerID)` → All batches for a farmer
- `GetBatchLifecycleEvents(batchID)` → Timeline of events
- `GetTransportsByBatch(batchID)` → All shipments for a batch
- `GetTransportTemperatureLogs(transportID)` → Temperature history
- `GetCertificationsByProcessing(processingID)` → All certifications
- `GetRegulatoryRecordsByBatch(batchID)` → All regulatory records

## Upgrade Strategy

### Version 1.0 → 2.0 Upgrade

1. **Backward Compatibility**: New chaincode can read v1.0 assets
2. **Schema Evolution**: Add optional fields with defaults
3. **No Data Loss**: Existing ledger immutable; new code reads it correctly

```go
// ✅ Safe: New field with sensible default
type ProcessingAsset struct {
    ...
    QualityScore float64 `json:"quality_score"`  // v1.0
    QualityGrade string  `json:"quality_grade"`  // v2.0 (new)
}
```

## Performance Considerations

### Throughput Optimization

- **Parallel Batch Creation**: Multiple farmers create batches simultaneously
- **Event Filtering**: Regulators query only pending certifications
- **Lifecycle Queries**: Retrieve full audit trail efficiently via CouchDB

### Scalability

- **Composite Keys**: Use `docType` for efficient filtering
- **Pagination**: Client loops through `GetQueryResultsForQueryString` iterator
- **Index Design**: CouchDB automatically indexes by `docType` + field combinations

## Integration with FastAPI Backend

### Data Flow

```
FastAPI (Python)                Hyperledger Fabric (Go)
┌──────────────────┐           ┌──────────────────────┐
│ Batch created    │──POST──→  │ CreateBatch          │
│ (DB insert)      │  /batch   │ (Ledger write)       │
└──────────────────┘           └──────────────────────┘
        │                               │
        │                               ↓
        │                          Consensus
        │                               ↓
        │                          CouchDB
        │                               │
        ├─ Query: SELECT * FROM batch ←┤
        │  (operational data)    │      │
        │                         └─→ Consumer can verify
        │                            on blockchain via
        │                            gateway SDK
        └─────────────────────────────→
```

**Key Points**:

- Database → Blockchain is **write-once** (fire and forget)
- No read-from-blockchain in FastAPI (unnecessary latency)
- FastAPI reads its own database for operational queries
- Consumer verification queries go through Fabric Gateway SDK

## Security Considerations

### 1. Input Sanitization

All string inputs validated for:

- Empty strings
- Malicious JSON injection (inputs are treated as values, not code)
- Excessive lengths

### 2. MSP-Based Access Control

No shared "admin password". Each org has X.509 certificate embedded in transactions.

### 3. Audit Trail

All state changes recorded:

- Timestamp (Fabric TxTimestamp)
- Actor (MSP ID from certificate)
- Change (before/after in diff)

### 4. Append-Only Logs

Violations/rejections cannot be hidden or modified.

## Testing Strategy

### Unit Tests (go test)

```
✓ CreateProduct authorization (regulator only)
✓ Batch creation with uniqueness check
✓ Lifecycle event immutability
✓ Temperature violation auto-flagging
✓ Certification workflow enforcement
✓ Status transition validation
✓ Input validation (empty strings, negatives)
```

### Integration Tests (fabric-samples test-network)

1. Deploy chaincode to test-network
2. Invoke through peer CLI
3. Query ledger state
4. Verify events emitted

### Chaos Tests

- Network partition (orderer unavailable)
- Peer failure (rejoin cluster)
- Concurrent transactions (determinism check)

## Deployment Checklist

- [ ] go.mod dependencies resolved
- [ ] Unit tests pass locally (go test ./...)
- [ ] Code follows determinism rules
- [ ] Events are sparse (only critical changes)
- [ ] Authorization checks in every function
- [ ] Validation before state access
- [ ] Error messages are helpful
- [ ] Upgrade plan documented
- [ ] Integration with FastAPI tested
- [ ] Fabric test-network deployment verified

## Future Enhancements

### Phase 2: Consumer API

```
/blockchain/batch/{batchID}           → Full lifecycle audit trail
/blockchain/farmer/{farmerID}/history → Farmer compliance history
/blockchain/verify/{productQR}        → Verify product origin
```

### Phase 3: Advanced Queries

- Complex audit trail filters
- Farmer reputation scoring
- Supply chain anomaly detection
- Predictive quality alerts

### Phase 4: Privacy-Preserving Features

- Private data collections (Fabric PDC)
- Zero-knowledge proofs for sensitive data
- Encrypted lifecycle events
