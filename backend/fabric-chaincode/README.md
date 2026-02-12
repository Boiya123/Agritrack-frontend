# AgriTrack Hyperledger Fabric Chaincode

**Production-ready Go chaincode** for agricultural supply chain traceability, implementing deterministic state management, access control, and immutable audit trails.

## Quick Start

### 1. Prerequisites

```bash
# Install Go 1.20+
go version

# Install Fabric tools
curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh
chmod +x install-fabric.sh
./install-fabric.sh
```

### 2. Test Locally

```bash
cd fabric-chaincode

# Run all unit tests
go test ./... -v

# Run specific test
go test -run TestCreateBatch -v

# Check code coverage
go test ./... -cover
```

### 3. Deploy to test-network

```bash
# From fabric-samples/test-network
./network.sh up createChannel -c mychannel -ca -s couchdb

# Follow deployment guide in DEPLOYMENT.md
```

### 4. Invoke Your First Transaction

```bash
# Create a product
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateProduct","Args":["prod-001","Poultry","Chicken"]}' \
  --tls --cafile $ORDERER_CA

# Create a batch
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateBatch","Args":["batch-001","prod-001","farmer-001","BATCH-2026-001","1000","2026-01-01","2026-02-01","Farm Alpha","QR-BATCH-001","Healthy flock"]}' \
  --tls --cafile $ORDERER_CA

# Query the batch
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatch","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

## Project Structure

```
fabric-chaincode/
├── chaincode/
│   ├── supplychain.go          # Main contract implementation (1000+ lines)
│   └── go.mod                  # Dependencies
├── test/
│   └── supplychain_test.go     # Unit tests (600+ lines, 15+ test cases)
├── scripts/
│   └── [deployment helpers]
├── DEPLOYMENT.md               # Complete deployment guide
├── CLI_COMMANDS.md             # CLI invoke/query examples
├── ARCHITECTURE.md             # Design & patterns
└── README.md                   # This file
```

## Key Features

### 🔐 Access Control

- **Role-based**: FarmOrg, RegulatorOrg, AdminOrg
- **MSP-based**: Fabric X.509 certificates enforce roles
- **No shared passwords**: Each org has unique identity

### 📝 Immutable Audit Trail

- **Append-only events**: Vaccinations, medications, mortalities
- **Permanent compliance records**: Failed certifications, rejections
- **Consumer transparency**: QR code → full supply chain history

### 🌡️ Cold Chain Monitoring

- **Auto-violation detection**: Temperatures outside 2-8°C flagged
- **Complete log**: Every temperature reading stored
- **Event alerts**: Violations trigger blockchain events

### 🔄 Deterministic Execution

- **No time.Now()**: Uses Fabric timestamps
- **No randomness**: All decisions validation-based
- **No external calls**: Pure on-chain logic

### 📊 Rich Queries

- Get batches by farmer
- Get lifecycle events by batch
- Get transports by batch
- Get certifications by processing
- Get regulatory records by batch

### ✅ Business Rules Enforcement

- Batch numbers must be unique
- Status transitions follow valid paths
- Quantities must be positive
- References must exist (referential integrity)

## Data Model

### 8 Asset Types

| Asset                   | Purpose                  | Mutable           | Examples                           |
| ----------------------- | ------------------------ | ----------------- | ---------------------------------- |
| **ProductAsset**        | Product type definitions | ✗ Deactivate only | Poultry, Rice, Corn                |
| **BatchAsset**          | Production groups        | ✓ Status updates  | Flock-2026-001                     |
| **LifecycleEventAsset** | Append-only audit trail  | ✗ Never           | Vaccination, Medication, Mortality |
| **TransportAsset**      | Shipment manifests       | ✓ Status updates  | Truck-001 departure                |
| **TemperatureLogAsset** | Cold chain readings      | ✗ Never           | 5.2°C at warehouse                 |
| **ProcessingAsset**     | Facility output          | ✓ Status updates  | Slaughter count, yield             |
| **CertificationAsset**  | Quality/safety certs     | ✓ Status updates  | FSMA, Health, Organic              |
| **RegulatoryAsset**     | Approvals/permits        | ✓ Status updates  | Export permit, Inspection          |

## Core Functions

### Products (Regulator)

```go
CreateProduct(productID, name, description)
GetProduct(productID)
DeactivateProduct(productID)
```

### Batches (Farmer)

```go
CreateBatch(batchID, productID, farmerID, batchNumber, quantity, ...)
GetBatch(batchID)
UpdateBatchStatus(batchID, newStatus)
CompleteBatch(batchID, actualEndDate)
GetBatchesByFarmer(farmerID)
```

### Lifecycle (Farmer)

```go
RecordLifecycleEvent(eventID, batchID, eventType, description, ...)
GetBatchLifecycleEvents(batchID)
```

### Transport (Farmer)

```go
CreateTransportManifest(transportID, batchID, fromParty, toParty, ...)
UpdateTransportStatus(transportID, newStatus, arrivalTime)
GetTransport(transportID)
GetTransportsByBatch(batchID)
AddTemperatureLog(logID, transportID, temperature, timestamp, location)
GetTransportTemperatureLogs(transportID)
```

### Processing (Farmer)

```go
RecordProcessing(processingID, batchID, facility, count, yield, ...)
GetProcessingRecord(processingID)
```

### Certification (Regulator)

```go
IssueCertification(certID, processingID, certType, ...)
UpdateCertificationStatus(certID, newStatus)
GetCertification(certID)
GetCertificationsByProcessing(processingID)
```

### Regulatory (Regulator)

```go
CreateRegulatoryRecord(regID, batchID, recordType, ...)
UpdateRegulatoryStatus(regID, newStatus, rejectionReason)
GetRegulatoryRecord(regID)
GetRegulatoryRecordsByBatch(batchID)
```

## Authorization Matrix

| Function               | FarmOrg | RegulatorOrg | AdminOrg |
| ---------------------- | ------- | ------------ | -------- |
| CreateProduct          | ✗       | ✓            | ✓        |
| CreateBatch            | ✓       | ✗            | ✓        |
| RecordLifecycleEvent   | ✓       | ✗            | ✓        |
| IssueCertification     | ✗       | ✓            | ✓        |
| CreateRegulatoryRecord | ✗       | ✓            | ✓        |
| GetBatch               | ✓       | ✓            | ✓        |

## Events Emitted

| Event                        | Triggered By                      | Payload                              |
| ---------------------------- | --------------------------------- | ------------------------------------ |
| BatchCreated                 | CreateBatch                       | batch_id, farmer_id                  |
| LifecycleEventRecorded       | RecordLifecycleEvent              | event_id, batch_id, event_type       |
| TransportCreated             | CreateTransportManifest           | transport_id, batch_id               |
| TemperatureViolationDetected | AddTemperatureLog (outside 2-8°C) | transport_id, temperature, threshold |
| ProcessingRecorded           | RecordProcessing                  | processing_id, batch_id              |
| CertificationUpdated         | Issue/Update certification        | certification_id, status             |
| RegulatoryRecordUpdated      | Create/Update regulatory          | regulatory_id, status                |

## Status Transitions

### Batch Lifecycle

```
CREATED --IN_PROGRESS--> COMPLETED (terminal)
   |           |
   |      FAILED ---+
   |           |    |
   |      (retry)---+
   |
   +--CANCELLED--> CANCELLED (terminal)
```

### Certification Lifecycle

```
APPROVED (issued directly)
PENDING --APPROVED--> (approved)
      |
      +--REJECTED--> (terminal)
```

### Regulatory Lifecycle

```
PENDING --APPROVED--> (approved)
      |
      +--REJECTED --> (reopen: PENDING)
```

## Examples

### Complete Workflow

```bash
# 1. Regulator creates product type
peer chaincode invoke CreateProduct prod-001 Poultry "Chicken production"

# 2. Farmer creates batch
peer chaincode invoke CreateBatch batch-001 prod-001 farmer-001 \
  BATCH-2026-001 1000 "2026-01-01" "2026-02-01" "Farm Alpha" "QR-001" ""

# 3. Farmer records vaccination event
peer chaincode invoke RecordLifecycleEvent event-001 batch-001 \
  VACCINATION "Vaccinated ND-IBV" farmer-001 "2026-01-05" 1000 \
  '{"vaccine":"ND-IBV"}'

# 4. Farmer records medication
peer chaincode invoke RecordLifecycleEvent event-002 batch-001 \
  MEDICATION "Antibiotic treatment" farmer-001 "2026-01-10" 50 \
  '{"medication":"Doxycycline"}'

# 5. Batch moves to processing facility
peer chaincode invoke UpdateBatchStatus batch-001 IN_PROGRESS

# 6. Transport begins (cold chain starts)
peer chaincode invoke CreateTransportManifest trans-001 batch-001 \
  farmer-001 supplier-001 truck-001 "John Doe" "2026-02-01T08:00:00Z" \
  "Farm Alpha" "Plant Beta" true ""

# 7. Temperature readings during transport
peer chaincode invoke AddTemperatureLog log-001 trans-001 \
  5.0 "2026-02-01T08:30:00Z" "Warehouse"  # OK

peer chaincode invoke AddTemperatureLog log-002 trans-001 \
  10.5 "2026-02-01T09:00:00Z" "Highway"   # VIOLATION!

# 8. Batch arrives and processing begins
peer chaincode invoke UpdateTransportStatus trans-001 COMPLETED "2026-02-01T12:00:00Z"

# 9. Processing facility records output
peer chaincode invoke RecordProcessing proc-001 batch-001 \
  "2026-02-01" "Plant Beta" 950 1200.5 95.0 ""

# 10. Regulator issues certifications
peer chaincode invoke IssueCertification cert-001 proc-001 \
  FOOD_SAFETY_CERT "2026-02-01" "2027-02-01" regulator-001 ""

# 11. Regulatory approval
peer chaincode invoke CreateRegulatoryRecord reg-001 batch-001 \
  EXPORT_PERMIT "2026-02-01" "2027-02-01" regulator-001 "Export OK" ""

peer chaincode invoke UpdateRegulatoryStatus reg-001 APPROVED ""

# 12. Complete batch
peer chaincode invoke CompleteBatch batch-001 "2026-02-01T14:00:00Z"

# 13. Consumer verifies via blockchain
peer chaincode query GetBatchLifecycleEvents batch-001
# → Full audit trail with all events
```

## Testing

### Unit Tests

```bash
cd fabric-chaincode
go test ./... -v

# Output:
# === RUN   TestCreateProduct
# === RUN   TestCreateProductUnauthorized
# === RUN   TestCreateBatch
# === RUN   TestLifecycleEventImmutability
# === RUN   TestTemperatureViolationDetection
# === RUN   TestCertificationRegulatoryEnforcement
# === RUN   TestRegulatoryApprovalWorkflow
# === RUN   TestValidationRules
# === RUN   TestDeterministicBehavior
# === RUN   TestStatusTransitionValidation
# === RUN   TestUniqueConstraints
# === RUN   TestAuthorizeMSP
# === RUN   BenchmarkCreateBatch
```

### Integration Tests (test-network)

Follow **DEPLOYMENT.md** to deploy and test on Fabric network.

## Documentation

| Document                           | Purpose                                                  |
| ---------------------------------- | -------------------------------------------------------- |
| [DEPLOYMENT.md](DEPLOYMENT.md)     | Step-by-step deployment guide with test-network          |
| [CLI_COMMANDS.md](CLI_COMMANDS.md) | 80+ invoke/query examples by role and use case           |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design patterns, determinism, security, upgrade strategy |
| [README.md](README.md)             | This quick reference                                     |

## Integration with FastAPI

### Data Sync Pattern

```
FastAPI                          Hyperledger Fabric
├─ POST /batch                   ├─ CreateBatch
│   ├─ INSERT DB                 │   ├─ Validate
│   └─ INVOKE blockchain  ─────→ │   └─ Write ledger
│
├─ GET /batch/{id}               └─ Query ledger via
│   └─ SELECT DB                    Gateway SDK
│
└─ Consumer                       └─ QR code
   └─ Verify product             → GetBatchLifecycleEvents
      history                       (immutable audit trail)
```

**Key Points**:

- Database is source of truth for operations
- Blockchain is source of truth for audit & compliance
- No read-from-blockchain in API (unnecessary latency)
- Consumer verification goes direct via Fabric Gateway SDK

## Performance Characteristics

- **Throughput**: ~1000 tx/sec per channel (Fabric v2.5)
- **Latency**: 200-500ms per block (depends on block size)
- **Query Speed**: <100ms for CouchDB queries
- **State Size**: ~500 bytes per asset (JSON)

## Security Checklist

- [x] No time.Now() (uses Fabric timestamps)
- [x] No randomness (deterministic validation)
- [x] No external calls (pure on-chain logic)
- [x] Input validation (empty strings, negatives, types)
- [x] Referential integrity (batches must exist)
- [x] Authorization checks (MSP-based)
- [x] Status machine enforcement (valid transitions only)
- [x] Append-only audit logs (immutable compliance records)
- [x] Event emission (critical state changes only)

## Troubleshooting

### Build Errors

```bash
# Missing dependencies
go mod tidy
go build ./...
```

### Authorization Failures

```bash
# Verify you're using the correct org
export CORE_PEER_LOCALMSPID="Org1MSP"  # Farmer
export CORE_PEER_LOCALMSPID="Org2MSP"  # Regulator
```

### Chaincode Not Found

```bash
# Ensure chaincode is committed to channel
peer lifecycle chaincode querycommitted -C mychannel
```

## Contributing

1. Write unit tests first
2. Run `go fmt` and `go vet`
3. Ensure all tests pass
4. Update documentation
5. Create PR with description

## License

MIT

## Support

- **Issues**: Create GitHub issue
- **Questions**: Email agritrack-team@example.com
- **Fabric Docs**: https://hyperledger-fabric.readthedocs.io/
