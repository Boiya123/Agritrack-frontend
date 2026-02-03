# AgriTrack Chaincode CLI Commands Reference

## Environment Setup

Before running any commands, set up the Fabric environment:

```bash
cd /path/to/fabric-samples/test-network

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

## Org1 (Farmer) Commands

### Product Management (Regulator)

#### Create Product

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateProduct","Args":["prod-001","Poultry","Chicken and egg production"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Product

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetProduct","Args":["prod-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

### Batch Management

#### Create Batch

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateBatch","Args":["batch-001","prod-001","farmer-001","BATCH-2026-001","1000","2026-01-01","2026-02-01","Farm Alpha","QR-BATCH-001","Healthy flock starting production"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Batch

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatch","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

#### Update Batch Status

```bash
# Transition from CREATED to IN_PROGRESS
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateBatchStatus","Args":["batch-001","IN_PROGRESS"]}' \
  --tls --cafile $ORDERER_CA
```

#### Complete Batch

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CompleteBatch","Args":["batch-001","2026-02-01T16:30:00Z"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Batches by Farmer

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatchesByFarmer","Args":["farmer-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

### Lifecycle Events (Append-Only)

#### Record Vaccination Event

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"RecordLifecycleEvent","Args":["event-001","batch-001","VACCINATION","Vaccinated with ND-IBV vaccine","farmer-001","2026-01-05T09:00:00Z","1000","{\"vaccine\":\"ND-IBV\",\"batch_size\":1000}"]}' \
  --tls --cafile $ORDERER_CA
```

#### Record Medication Event

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"RecordLifecycleEvent","Args":["event-002","batch-001","MEDICATION","Treated for respiratory infection","farmer-001","2026-01-10T14:30:00Z","50","{\"medication\":\"Doxycycline\",\"animals_treated\":50}"]}' \
  --tls --cafile $ORDERER_CA
```

#### Record Mortality Event

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"RecordLifecycleEvent","Args":["event-003","batch-001","MORTALITY","Natural mortality recorded","farmer-001","2026-01-15T08:00:00Z","5","{\"cause\":\"natural\",\"count\":5}"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Lifecycle Events for Batch

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatchLifecycleEvents","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

### Transport & Logistics

#### Create Transport Manifest

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateTransportManifest","Args":["trans-001","batch-001","farmer-001","supplier-001","truck-001","John Doe","2026-02-01T08:00:00Z","Farm Alpha","Processing Plant","true","Cold chain transport"]}' \
  --tls --cafile $ORDERER_CA
```

#### Update Transport Status

```bash
# Mark as in-transit
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateTransportStatus","Args":["trans-001","IN_TRANSIT",""]}' \
  --tls --cafile $ORDERER_CA

# Mark as completed with arrival time
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateTransportStatus","Args":["trans-001","COMPLETED","2026-02-01T12:30:00Z"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Transport

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetTransport","Args":["trans-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

#### Add Temperature Reading (Safe Range)

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"AddTemperatureLog","Args":["log-001","trans-001","5.0","2026-02-01T08:30:00Z","Warehouse Entrance"]}' \
  --tls --cafile $ORDERER_CA
```

#### Add Temperature Reading (Violation - Too Cold)

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"AddTemperatureLog","Args":["log-002","trans-001","0.5","2026-02-01T09:00:00Z","Highway"]}' \
  --tls --cafile $ORDERER_CA
# This will emit TemperatureViolationDetected event
```

#### Add Temperature Reading (Violation - Too Warm)

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"AddTemperatureLog","Args":["log-003","trans-001","12.0","2026-02-01T09:30:00Z","Rest Stop"]}' \
  --tls --cafile $ORDERER_CA
# This will emit TemperatureViolationDetected event
```

#### Get Temperature Logs for Transport

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetTransportTemperatureLogs","Args":["trans-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

#### Get Transports by Batch

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetTransportsByBatch","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

### Processing Records

#### Record Processing

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"RecordProcessing","Args":["proc-001","batch-001","2026-02-01T10:00:00Z","Plant Alpha","950","1200.5","95.0","All animals processed successfully"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Processing Record

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetProcessingRecord","Args":["proc-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

## Org2 (Regulator) Commands

Switch to Org2:

```bash
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
```

### Certification Management

#### Issue Certification (Regulator Only)

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"IssueCertification","Args":["cert-001","proc-001","FOOD_SAFETY_CERT","2026-02-01T15:00:00Z","2027-02-01T15:00:00Z","regulator-001","Passed all FSMA inspections"]}' \
  --tls --cafile $ORDERER_CA
```

#### Issue Health Certificate

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"IssueCertification","Args":["cert-002","proc-001","HEALTH_CERT","2026-02-01T15:00:00Z","2027-02-01T15:00:00Z","regulator-001","Animal health verified"]}' \
  --tls --cafile $ORDERER_CA
```

#### Update Certification Status

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateCertificationStatus","Args":["cert-001","APPROVED"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Certification

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetCertification","Args":["cert-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

#### Get Certifications by Processing

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetCertificationsByProcessing","Args":["proc-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

### Regulatory Records

#### Create Regulatory Record (Pending)

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateRegulatoryRecord","Args":["reg-001","batch-001","EXPORT_PERMIT","2026-02-01T10:00:00Z","2027-02-01T10:00:00Z","regulator-001","Export to EU approved","audit_flag_1:passed"]}' \
  --tls --cafile $ORDERER_CA
```

#### Approve Regulatory Record

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateRegulatoryStatus","Args":["reg-001","APPROVED",""]}' \
  --tls --cafile $ORDERER_CA
```

#### Reject Regulatory Record

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateRegulatoryStatus","Args":["reg-001","REJECTED","Temperature violations detected during transport"]}' \
  --tls --cafile $ORDERER_CA
```

#### Get Regulatory Record

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetRegulatoryRecord","Args":["reg-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

#### Get Regulatory Records by Batch

```bash
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetRegulatoryRecordsByBatch","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq .
```

## Query Examples (Any Organization)

### Search by Status

```bash
# Find all IN_PROGRESS batches
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatchesByFarmer","Args":["farmer-001"]}' \
  --tls --cafile $ORDERER_CA | jq '.[] | select(.status=="IN_PROGRESS")'
```

### Historical Audit Trail

```bash
# Get complete lifecycle for a batch
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatchLifecycleEvents","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq 'sort_by(.created_at)'
```

### Chain of Custody

```bash
# Get all transports for a batch
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetTransportsByBatch","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA

# Then for each transport, check temperatures
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetTransportTemperatureLogs","Args":["trans-001"]}' \
  --tls --cafile $ORDERER_CA | jq '.[] | select(.is_violation==true)'
```

## Event Monitoring

Listen for emitted events:

```bash
# In separate terminal, watch for events
peer chaincode query -C mychannel -n agritrack \
  -c '{"function":"GetBatchLifecycleEvents","Args":["batch-001"]}' \
  --tls --cafile $ORDERER_CA | jq '.' > /tmp/events.log

# Watch log in real-time
tail -f /tmp/events.log
```

## Error Handling Examples

### Unauthorized Action (Farmer tries to certify)

```bash
# Switch to Org1 (Farmer)
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Try to issue certification (should fail)
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"IssueCertification","Args":["cert-003","proc-001","FOOD_SAFETY_CERT","2026-02-01T15:00:00Z","2027-02-01T15:00:00Z","farmer-001","Passed"]}' \
  --tls --cafile $ORDERER_CA
# Response: "unauthorized: MSP FarmOrgMSP not allowed"
```

### Duplicate Batch Number

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"CreateBatch","Args":["batch-002","prod-001","farmer-001","BATCH-2026-001","500","2026-01-10","2026-02-10","Farm Beta","QR-002","Another batch"]}' \
  --tls --cafile $ORDERER_CA
# Response: "batch number BATCH-2026-001 already exists"
```

### Invalid Status Transition

```bash
peer chaincode invoke -C mychannel -n agritrack \
  -c '{"function":"UpdateBatchStatus","Args":["batch-001","CANCELLED"]}' \
  --tls --cafile $ORDERER_CA
# If current status is COMPLETED:
# Response: "invalid transition from COMPLETED to CANCELLED"
```

## Tips & Best Practices

1. **Use jq for Pretty Output**: Pipe queries to `jq .` for formatted JSON
2. **Capture TxID**: Add `--transient` to capture transaction ID for audit
3. **Check Ledger State**: Query after invoke to verify state change
4. **Monitor Peer Logs**: `docker logs peer0.org1.example.com` for debugging
5. **Test with Batch**: Write scripts to test complete workflows
6. **Use Timestamps**: Always include ISO 8601 timestamps for audit trails
7. **Validate References**: Ensure batch exists before creating events
8. **Check MSP**: Ensure you're using correct organization for operation
