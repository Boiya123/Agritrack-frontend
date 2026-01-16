# Hyperledger Blockchain Integration Guide

## Overview

AgriTrack uses Hyperledger Fabric as an immutable audit trail for agricultural traceability. This ensures transparency and builds consumer trust by creating permanent records that cannot be modified or deleted.

## Data Flow Architecture

```
AgriTrack Database (Source of Truth)
         ↓
  [Critical Event Occurs]
  - Certification Failed
  - Disease Reported
  - Regulatory Violation
  - Quality Check Failed
         ↓
  [Event Listener Triggered]
  (lifecycle_routes.py, processing_routes.py, regulatory_routes.py)
         ↓
  [Message Queue]
  (RabbitMQ/Kafka for async processing)
         ↓
  [Hyperledger Fabric Writer]
  (blockchain_service.py - future)
         ↓
  [Immutable Blockchain Record]
  (append-only, auditable, consumer-accessible)
```

## What Gets Written to Blockchain

### 1. Farmer Compliance Records

- Certification pass/fail records
- Regulatory violations
- Audit results
- Health violations

**Example Blockchain Record:**

```json
{
  "type": "FARMER_COMPLIANCE",
  "farmer_id": "uuid",
  "event": "CERTIFICATION_FAILED",
  "certification_type": "FOOD_SAFETY_CERT",
  "reason": "Failed temperature control audit",
  "timestamp": "2026-01-17T10:30:00Z",
  "regulator_id": "uuid",
  "severity": "CRITICAL"
}
```

### 2. Batch Lifecycle Events

- Disease/illness outbreaks
- Mortality rates exceeding threshold
- Production issues
- Quality failures

**Example Blockchain Record:**

```json
{
  "type": "BATCH_EVENT",
  "batch_id": "uuid",
  "farmer_id": "uuid",
  "event": "DISEASE_OUTBREAK",
  "disease_type": "AVIAN_FLU",
  "affected_count": 150,
  "timestamp": "2026-01-17T14:22:00Z",
  "lifecycle_record_id": "uuid"
}
```

### 3. Chain-of-Custody Records

- Transport handoffs
- Facility transfers
- Temperature violations during logistics
- Custody changes

**Example Blockchain Record:**

```json
{
  "type": "CUSTODY_CHANGE",
  "batch_id": "uuid",
  "from_party": "farmer_uuid",
  "to_party": "supplier_uuid",
  "transport_id": "uuid",
  "timestamp": "2026-01-17T16:45:00Z",
  "temperature_violations": 0
}
```

## Implementation Roadmap

### Phase 1: Event Infrastructure (Current Development)

1. Create `app/services/blockchain_service.py` with event emitter abstraction
2. Add event listeners to critical route handlers
3. Implement event schema definitions

### Phase 2: Message Queue Setup

1. Install RabbitMQ/Kafka
2. Configure message queue in `app/core/config.py`
3. Create message producers for blockchain events
4. Build consumer workers for blockchain writes

### Phase 3: Hyperledger Integration

1. Install Hyperledger Fabric SDK for Python
2. Implement chaincode interaction layer
3. Build connection management (wallets, network config)
4. Implement blockchain write operations

### Phase 4: Consumer API

1. Create `app/api/routes/blockchain_routes.py`
2. Implement farmer history query endpoints
3. Implement batch certification query endpoints
4. Add consumer-facing transparency endpoints

## Key Principles

### Immutability

- **No updates or deletes**: Only appends to blockchain
- Violations and failures create permanent public record
- Corrections require new records with "CORRECTION" type

### Transparency

- Farmers cannot hide compliance failures
- Consumers can verify farmer reliability
- Regulators have auditable trail

### Performance

- Use async message queues to avoid blocking API responses
- Batch blockchain writes periodically if needed
- Cache blockchain queries for frequently accessed data

### Fault Tolerance

- Failed blockchain writes go to retry queue
- API responses succeed even if blockchain temporarily unavailable
- Periodic reconciliation job ensures eventual consistency

## Future Enhancements

- Consumer-facing mobile app for product history verification
- QR codes linking to blockchain records
- Real-time compliance dashboard for regulators
- Farmer reputation scoring based on blockchain history
- Automated alerts for compliance violations
