# FastAPI & Hyperledger Blockchain Integration Guide

## Overview

This guide covers integrating the AgriTrack FastAPI backend with the Hyperledger Fabric blockchain for immutable record-keeping and supply chain transparency.

## Architecture

### Data Flow

```
FastAPI Backend
    ↓
  [Business Logic: create batch, record event, etc.]
    ↓
  [Event Listener / Trigger]
    ↓
  [Message Queue - RabbitMQ/Kafka]
    ↓
  [Blockchain Writer Service]
    ↓
  [Hyperledger Fabric Chaincode]
    ↓
  [Immutable Ledger]
```

### Integration Points

1. **Critical Events** → Database → Blockchain
   - Certification failures
   - Disease outbreaks
   - Regulatory violations
   - Quality failures

2. **Transparent Queries** → Blockchain → Consumers
   - Farmer history and compliance
   - Batch certifications
   - Transport chain-of-custody

## Prerequisites

### Python Packages

```bash
# Core blockchain connectivity
pip install fabric-sdk-py==0.8.1

# Message queue for async processing
pip install pika==1.3.1          # RabbitMQ
pip install kafka-python==2.0.2  # Kafka (alternative)

# Async task processing
pip install celery==5.3.0
pip install redis==5.0.0
```

### Fabric SDK Configuration

- **Fabric CA Python SDK** for user enrollment
- **Peer SDK** for chaincode invocation
- Network config file (YAML) pointing to Fabric peers/orderers

## Step 1: Install Fabric SDK

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Fabric SDK
pip install fabric-sdk-py

# Verify installation
python3 -c "import hfc; print(hfc.__version__)"
```

## Step 2: Create Blockchain Service Module

Create `app/services/blockchain_service.py`:

```python
from typing import Dict, List, Optional, Any
from hfc.fabric import Client
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.util.util import ensure_bytes
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class BlockchainService:
    """Manages Hyperledger Fabric blockchain interactions"""

    def __init__(self, config_path: str):
        """
        Initialize blockchain service

        Args:
            config_path: Path to Fabric network config (e.g., ./fabric-network-config.yaml)
        """
        self.client = Client(net_profile=config_path)
        self.channel_name = "agritrack-channel"
        self.chaincode_name = "agritrack"
        self.channel = None

    async def initialize(self):
        """Initialize connection to Fabric network"""
        try:
            self.channel = self.client.get_channel(self.channel_name)
            if not self.channel:
                self.channel = self.client.new_channel(self.channel_name)
            logger.info(f"Connected to channel: {self.channel_name}")
        except Exception as e:
            logger.error(f"Failed to initialize blockchain connection: {e}")
            raise

    async def record_farmer_compliance(
        self,
        farmer_id: str,
        event_type: str,  # "CERTIFICATION_PASSED", "CERTIFICATION_FAILED", "VIOLATION"
        details: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record farmer compliance event on blockchain

        Args:
            farmer_id: UUID of farmer
            event_type: Type of compliance event
            details: Event-specific details (reason, severity, etc.)
            timestamp: ISO 8601 timestamp (auto-generated if not provided)

        Returns:
            Transaction result with txID
        """
        if not timestamp:
            timestamp = datetime.utcnow().isoformat() + "Z"

        payload = {
            "type": "FARMER_COMPLIANCE",
            "farmer_id": farmer_id,
            "event": event_type,
            "timestamp": timestamp,
            **details
        }

        try:
            # Invoke chaincode function
            response = await self._invoke_chaincode(
                "RecordFarmerCompliance",
                [json.dumps(payload)]
            )
            logger.info(f"Recorded farmer compliance: {farmer_id} - {event_type}")
            return {"status": "success", "tx_id": response}
        except Exception as e:
            logger.error(f"Failed to record farmer compliance: {e}")
            raise

    async def record_batch_event(
        self,
        batch_id: str,
        farmer_id: str,
        event_type: str,  # "DISEASE_OUTBREAK", "MORTALITY", "QUALITY_FAILURE"
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record batch lifecycle event on blockchain"""
        payload = {
            "type": "BATCH_EVENT",
            "batch_id": batch_id,
            "farmer_id": farmer_id,
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **details
        }

        try:
            response = await self._invoke_chaincode(
                "RecordBatchEvent",
                [json.dumps(payload)]
            )
            logger.info(f"Recorded batch event: {batch_id} - {event_type}")
            return {"status": "success", "tx_id": response}
        except Exception as e:
            logger.error(f"Failed to record batch event: {e}")
            raise

    async def record_custody_change(
        self,
        batch_id: str,
        from_party: str,  # MSP ID or party identifier
        to_party: str,
        transport_id: str,
        temperature_violations: int = 0
    ) -> Dict[str, Any]:
        """Record chain-of-custody transfer on blockchain"""
        payload = {
            "type": "CUSTODY_CHANGE",
            "batch_id": batch_id,
            "from_party": from_party,
            "to_party": to_party,
            "transport_id": transport_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature_violations": temperature_violations
        }

        try:
            response = await self._invoke_chaincode(
                "RecordCustodyChange",
                [json.dumps(payload)]
            )
            logger.info(f"Recorded custody change: {batch_id}")
            return {"status": "success", "tx_id": response}
        except Exception as e:
            logger.error(f"Failed to record custody change: {e}")
            raise

    async def query_farmer_history(self, farmer_id: str) -> List[Dict]:
        """Query complete compliance history of a farmer"""
        try:
            result = await self._query_chaincode(
                "GetFarmerHistory",
                [farmer_id]
            )
            return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to query farmer history: {e}")
            raise

    async def query_batch_certifications(self, batch_id: str) -> List[Dict]:
        """Query all certifications for a batch"""
        try:
            result = await self._query_chaincode(
                "GetBatchCertifications",
                [batch_id]
            )
            return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to query batch certifications: {e}")
            raise

    async def _invoke_chaincode(
        self,
        function: str,
        args: List[str],
        timeout: int = 30
    ) -> str:
        """
        Invoke chaincode function (write operation)

        Args:
            function: Chaincode function name
            args: Function arguments
            timeout: Operation timeout in seconds

        Returns:
            Transaction ID
        """
        try:
            # Proposal request
            proposal = {
                'fcn': function,
                'args': args
            }

            # Send to endorsers
            peers = self.channel.get_peers()
            response = await asyncio.wait_for(
                self._send_proposal(proposal, peers),
                timeout=timeout
            )

            # Parse transaction ID from response
            if response and len(response) > 0:
                tx_id = response[0].get('txID')
                return tx_id
            else:
                raise Exception("No endorsement received")

        except asyncio.TimeoutError:
            logger.error(f"Chaincode invocation timeout: {function}")
            raise
        except Exception as e:
            logger.error(f"Chaincode invocation failed: {function} - {e}")
            raise

    async def _query_chaincode(
        self,
        function: str,
        args: List[str],
        timeout: int = 10
    ) -> str:
        """
        Query chaincode (read-only operation)

        Args:
            function: Chaincode function name
            args: Function arguments
            timeout: Operation timeout in seconds

        Returns:
            Query result as JSON string
        """
        try:
            proposal = {
                'fcn': function,
                'args': args
            }

            peers = self.channel.get_peers()
            response = await asyncio.wait_for(
                self._send_query(proposal, peers),
                timeout=timeout
            )

            if response and len(response) > 0:
                return response[0]
            else:
                return "[]"

        except asyncio.TimeoutError:
            logger.error(f"Chaincode query timeout: {function}")
            raise
        except Exception as e:
            logger.error(f"Chaincode query failed: {function} - {e}")
            raise

    async def _send_proposal(self, proposal: Dict, peers: List) -> List:
        """Send endorsement proposal to peers"""
        # Implementation delegated to Fabric SDK
        pass

    async def _send_query(self, proposal: Dict, peers: List) -> List:
        """Send query proposal to peers"""
        # Implementation delegated to Fabric SDK
        pass
```

## Step 3: Create Event Listeners

Create `app/services/blockchain_events.py`:

```python
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.blockchain_service import BlockchainService

class BlockchainEventType(Enum):
    """Critical events that trigger blockchain writes"""
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    DISEASE_OUTBREAK = "DISEASE_OUTBREAK"
    REGULATORY_VIOLATION = "REGULATORY_VIOLATION"
    QUALITY_FAILURE = "QUALITY_FAILURE"
    CUSTODY_TRANSFER = "CUSTODY_TRANSFER"

class BlockchainEventListener:
    """Listens for critical events and writes to blockchain"""

    def __init__(self, blockchain_service: BlockchainService):
        self.blockchain = blockchain_service

    async def on_certification_result(
        self,
        farmer_id: str,
        certification_type: str,
        status: str,  # "PASSED" or "FAILED"
        reason: Optional[str] = None
    ):
        """Called when certification is issued"""
        if status == "FAILED":
            await self.blockchain.record_farmer_compliance(
                farmer_id=farmer_id,
                event_type="CERTIFICATION_FAILED",
                details={
                    "certification_type": certification_type,
                    "reason": reason,
                    "severity": "CRITICAL"
                }
            )

    async def on_disease_reported(
        self,
        batch_id: str,
        farmer_id: str,
        disease_type: str,
        affected_count: int,
        mortality_rate: float
    ):
        """Called when disease is detected in batch"""
        await self.blockchain.record_batch_event(
            batch_id=batch_id,
            farmer_id=farmer_id,
            event_type="DISEASE_OUTBREAK",
            details={
                "disease_type": disease_type,
                "affected_count": affected_count,
                "mortality_rate": mortality_rate,
                "severity": "CRITICAL" if mortality_rate > 0.1 else "MAJOR"
            }
        )

    async def on_regulatory_violation(
        self,
        farmer_id: str,
        violation_type: str,
        severity: str,
        details: Dict[str, Any]
    ):
        """Called when regulator records violation"""
        await self.blockchain.record_farmer_compliance(
            farmer_id=farmer_id,
            event_type="REGULATORY_VIOLATION",
            details={
                "violation_type": violation_type,
                "severity": severity,
                **details
            }
        )

    async def on_custody_transfer(
        self,
        batch_id: str,
        from_party: str,
        to_party: str,
        transport_id: str,
        temperature_violations: int = 0
    ):
        """Called when batch custody changes (transport, facility)"""
        await self.blockchain.record_custody_change(
            batch_id=batch_id,
            from_party=from_party,
            to_party=to_party,
            transport_id=transport_id,
            temperature_violations=temperature_violations
        )
```

## Step 4: Integrate Events into Routes

Update `app/api/routes/regulatory_routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.services.blockchain_events import BlockchainEventListener, BlockchainEventType
from app.models.user_model import User

router = APIRouter(prefix="/regulatory", tags=["regulatory"])

# Initialize event listener
blockchain_listener = None  # Injected at startup

@router.post("/violation/{farmer_id}")
async def report_violation(
    farmer_id: str,
    violation_type: str,
    severity: str,  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report regulatory violation"""

    # Check authorization
    if current_user.role != UserRole.REGULATOR:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Save to database
    violation = RegulatoryRecord(
        farmer_id=farmer_id,
        violation_type=violation_type,
        severity=severity,
        regulator_id=current_user.id
    )
    db.add(violation)
    db.commit()

    # Record on blockchain (async, non-blocking)
    if blockchain_listener:
        await blockchain_listener.on_regulatory_violation(
            farmer_id=farmer_id,
            violation_type=violation_type,
            severity=severity,
            details={"regulator_id": str(current_user.id)}
        )

    return violation
```

## Step 5: Setup Message Queue (Optional but Recommended)

For production, use RabbitMQ to decouple blockchain writes:

### Install RabbitMQ

```bash
# macOS
brew install rabbitmq

# Linux
sudo apt-get install rabbitmq-server

# Docker
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

### Create Queue Producer

Create `app/services/blockchain_queue.py`:

```python
import pika
import json
from typing import Dict, Any

class BlockchainQueue:
    """Manages blockchain write queue"""

    def __init__(self, rabbitmq_url: str = "amqp://guest:guest@localhost/"):
        self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        self.channel = self.connection.channel()
        self.queue_name = "blockchain-events"
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def publish_event(self, event_type: str, payload: Dict[str, Any]):
        """Publish blockchain event to queue"""
        message = json.dumps({
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        })

        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

    def close(self):
        self.connection.close()
```

## Step 6: Fabric Network Configuration

Create `fabric-network-config.yaml`:

```yaml
name: AgriTrack
version: 1.0.0

client:
  organization: Org1
  credentialStore:
    path: /tmp/hfc-key-store

organizations:
  Org1:
    mspid: Org1MSP
    peers:
      - peer0.org1.example.com
    certificateAuthorities:
      - ca.org1.example.com

peers:
  peer0.org1.example.com:
    url: grpcs://localhost:7051
    tlsCACerts:
      path: /path/to/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

orderers:
  orderer.example.com:
    url: grpcs://localhost:7050
    tlsCACerts:
      path: /path/to/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

channels:
  agritrack-channel:
    orderers:
      - orderer.example.com
    peers:
      peer0.org1.example.com:
        endorsingPeer: true
        chaincodeQuery: true
        ledgerQuery: true
```

## Step 7: Add Startup Configuration

Update `app/main.py`:

```python
from fastapi import FastAPI
from app.services.blockchain_service import BlockchainService
from app.services.blockchain_events import BlockchainEventListener
import os
import asyncio

app = FastAPI(title="AgriTrack")

blockchain_service = None
blockchain_listener = None

@app.on_event("startup")
async def startup_event():
    global blockchain_service, blockchain_listener

    try:
        # Initialize blockchain service
        config_path = os.getenv(
            "FABRIC_CONFIG_PATH",
            "./fabric-network-config.yaml"
        )
        blockchain_service = BlockchainService(config_path)
        await blockchain_service.initialize()

        # Initialize event listener
        blockchain_listener = BlockchainEventListener(blockchain_service)

        print("✓ Blockchain service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize blockchain: {e}")
        # Continue without blockchain in dev mode

@app.on_event("shutdown")
async def shutdown_event():
    if blockchain_service:
        # Cleanup blockchain connections
        pass
```

## Testing Integration

```python
# test_blockchain_integration.py
import pytest
from app.services.blockchain_service import BlockchainService

@pytest.mark.asyncio
async def test_blockchain_connection():
    """Test blockchain service connectivity"""
    blockchain = BlockchainService("./fabric-network-config.yaml")
    await blockchain.initialize()
    assert blockchain.channel is not None

@pytest.mark.asyncio
async def test_record_compliance_event():
    """Test recording farmer compliance on blockchain"""
    blockchain = BlockchainService("./fabric-network-config.yaml")
    await blockchain.initialize()

    result = await blockchain.record_farmer_compliance(
        farmer_id="FARMER_001",
        event_type="CERTIFICATION_FAILED",
        details={"reason": "Temperature control failure"}
    )

    assert result["status"] == "success"
    assert "tx_id" in result
```

## Environment Variables

Add to `.env`:

```bash
# Blockchain Configuration
FABRIC_CONFIG_PATH=./fabric-network-config.yaml
FABRIC_CHANNEL_NAME=agritrack-channel
FABRIC_CHAINCODE_NAME=agritrack

# RabbitMQ (optional)
RABBITMQ_URL=amqp://guest:guest@localhost/
BLOCKCHAIN_QUEUE_ENABLED=true
```

## Monitoring & Debugging

### Enable Blockchain Logging

```python
import logging

# In main.py or config
logging.basicConfig(level=logging.DEBUG)
fabric_logger = logging.getLogger('hfc')
fabric_logger.setLevel(logging.DEBUG)
```

### Monitor Blockchain Events

```python
# Get transaction details
async def get_transaction_details(tx_id: str):
    """Query transaction from blockchain"""
    return await blockchain_service.client.get_tx(
        tx_id,
        channel_name="agritrack-channel"
    )
```

## Security Considerations

1. **User Enrollment**: Store CA credentials securely
2. **TLS**: Always use TLS for peer/orderer communication
3. **MSP Identity**: Verify organization MSP for all write operations
4. **Rate Limiting**: Implement rate limits for blockchain writes
5. **Error Handling**: Don't expose blockchain errors to clients

## Production Checklist

- [ ] Blockchain service initialized at startup
- [ ] Error handling prevents API crashes from blockchain failures
- [ ] Event listeners configured for all critical operations
- [ ] Message queue configured and monitored
- [ ] TLS certificates properly configured
- [ ] User enrollment and credential management in place
- [ ] Monitoring and alerting for blockchain failures
- [ ] Disaster recovery plan for lost blockchain connection
- [ ] Load testing with blockchain integration
- [ ] Audit logging for all blockchain operations

## Troubleshooting

### "Connection refused" to peer

- Ensure Fabric network is running: `./network.sh up`
- Check peer logs: `docker logs peer0.org1.example.com`
- Verify network config paths point to correct TLS certs

### "Endorsement policy mismatch"

- Confirm chaincode is committed: `peer lifecycle chaincode querycommitted`
- Check channel membership: `peer channel list`

### "MSP ID mismatch"

- Verify enrolled user's MSP matches organization
- Check credential store contains valid certificates

## Related Documentation

- [HYPERLEDGER_INTEGRATION.md](HYPERLEDGER_INTEGRATION.md)
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [BLOCKCHAIN_QUICK_REFERENCE.md](../BLOCKCHAIN_QUICK_REFERENCE.md)
