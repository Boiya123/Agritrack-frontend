"""
Example: Using Blockchain Service in Routes

This example demonstrates how to integrate the blockchain service
into your FastAPI route handlers following AgriTrack architecture principles.

Pattern:

1. API route handles database operations first (fast response)
2. Blockchain writes happen after (non-blocking)
3. Blockchain failures don't fail the API response
4. Service is never imported directly in routes
   """

import json
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User
from app.services.blockchain_service import (
initialize_blockchain_service,
BlockchainServiceError,
BlockchainConnectionError,
BlockchainTransactionError,
)

logger = logging.getLogger(**name**)

# Example router

router = APIRouter(prefix="/example", tags=["example-blockchain"])

# ==============================================================================

# Example 1: Record Farmer Compliance Event (Write Operation)

# ==============================================================================

class ComplianceEventCreate:
"""Example schema (use your actual schema)"""
farmer_id: UUID
certification_type: str
status: str
reason: Optional[str] = None

@router.post("/compliance-event")
async def record_compliance_event(
event_data: ComplianceEventCreate,
current_user: User = Depends(get_current_user),
db: Session = Depends(get_db)
):
"""
Record a farmer compliance event to both database and blockchain.

    API response is returned immediately after database commit.
    Blockchain write happens in background (non-blocking).
    """

    # STEP 1: Create database record (fast path)
    # (Your actual model and logic here)
    db_event = {
        "farmer_id": event_data.farmer_id,
        "certification_type": event_data.certification_type,
        "status": event_data.status,
        "reason": event_data.reason
    }
    # db.add(db_event)
    # db.commit()
    # db.refresh(db_event)

    # STEP 2: Return API response immediately
    api_response = {
        "id": "event-123",  # from db_event
        "farmer_id": str(event_data.farmer_id),
        "status": event_data.status,
        "message": "Compliance event recorded"
    }

    # STEP 3: Record to blockchain (fire and forget)
    # In production, use a message queue to decouple this further
    try:
        blockchain = initialize_blockchain_service()

        # Prepare arguments for chaincode function
        # All arguments must be strings
        args = [
            str(event_data.farmer_id),
            event_data.certification_type,
            event_data.status,
            event_data.reason or ""
        ]

        # Call blockchain (async, non-blocking)
        result = await blockchain.submit_transaction(
            "RecordFarmerComplianceEvent",  # Chaincode function name
            *args
        )
        logger.info(f"Compliance event recorded to blockchain: {result}")

    except BlockchainConnectionError as e:
        # Peer unavailable, certificate invalid, network error
        # Queue for retry instead of failing the API response
        logger.warning(f"Blockchain temporarily unavailable: {e}")
        # In production: add_to_retry_queue(event_data)

    except BlockchainTransactionError as e:
        # Chaincode execution failed
        # Usually a programming error in chaincode
        logger.error(f"Chaincode execution failed: {e}")
        # In production: alert_on_call_error(e)

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected blockchain error: {e}")

    # Return API response regardless of blockchain status
    return api_response

# ==============================================================================

# Example 2: Query Farmer History (Read Operation)

# ==============================================================================

@router.get("/farmer/{farmer_id}/history")
async def get_farmer_history(
farmer_id: UUID,
current_user: User = Depends(get_current_user)
):
"""
Query farmer compliance history from blockchain (read-only).
This is a public endpoint for transparency.
"""

    try:
        blockchain = initialize_blockchain_service()

        # Evaluate transaction (read-only, no ledger modification)
        history_json = await blockchain.evaluate_transaction(
            "GetFarmerHistory",
            str(farmer_id)
        )

        # Parse chaincode response
        history = json.loads(history_json)

        return {
            "farmer_id": str(farmer_id),
            "history": history,
            "source": "blockchain"
        }

    except BlockchainConnectionError as e:
        logger.error(f"Cannot reach blockchain: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service unavailable"
        )

    except BlockchainTransactionError as e:
        logger.error(f"Chaincode query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query failed: {e}"
        )

# ==============================================================================

# Example 3: Batch with Multiple Blockchain Events

# ==============================================================================

class BatchCreate:
"""Example schema"""
farmer_id: UUID
product_type: str
quantity: int
notes: Optional[str] = None

@router.post("/batch")
async def create_batch(
batch_data: BatchCreate,
current_user: User = Depends(get_current_user),
db: Session = Depends(get_db)
):
"""
Create a production batch, recording multiple events to blockchain.
Demonstrates handling multiple blockchain writes.
"""

    # Create batch in database
    # batch = Batch(**batch_data.dict(), farmer_id=current_user.id)
    # db.add(batch)
    # db.commit()
    # db.refresh(batch)
    batch_id = "batch-uuid-123"  # from db

    # Return API response
    api_response = {
        "id": batch_id,
        "farmer_id": str(batch_data.farmer_id),
        "status": "created"
    }

    # Record to blockchain asynchronously
    blockchain = initialize_blockchain_service()

    # Event 1: Batch created
    try:
        await blockchain.submit_transaction(
            "RecordBatchCreated",
            batch_id,
            str(batch_data.farmer_id),
            batch_data.product_type,
            str(batch_data.quantity)
        )
        logger.info(f"Batch creation recorded to blockchain: {batch_id}")
    except BlockchainServiceError as e:
        logger.warning(f"Failed to record batch creation: {e}")
        # Continue with other operations

    # Event 2: Initial inventory recorded
    try:
        await blockchain.submit_transaction(
            "RecordInventory",
            batch_id,
            "INITIAL",
            str(batch_data.quantity),
            batch_data.notes or ""
        )
        logger.info(f"Inventory recorded to blockchain: {batch_id}")
    except BlockchainServiceError as e:
        logger.warning(f"Failed to record inventory: {e}")

    return api_response

# ==============================================================================

# Example 4: Error Handling Pattern for Critical Operations

# ==============================================================================

@router.post("/disease-report")
async def report_disease_outbreak(
batch_id: UUID,
disease_type: str,
affected_count: int,
current_user: User = Depends(get_current_user),
db: Session = Depends(get_db)
):
"""
Report a disease outbreak.
This is a CRITICAL event that must be recorded on blockchain.

    Demonstrates: stricter error handling for critical events
    """

    # Create database record
    # disease_record = DiseaseRecord(batch_id=batch_id, type=disease_type, count=affected_count)
    # db.add(disease_record)
    # db.commit()

    # Record to blockchain with stricter error handling
    blockchain = initialize_blockchain_service()

    try:
        result = await blockchain.submit_transaction(
            "RecordDiseaseOutbreak",
            str(batch_id),
            disease_type,
            str(affected_count)
        )
        logger.critical(f"Disease outbreak recorded to blockchain: {result}")

    except BlockchainConnectionError as e:
        # For critical events, failing to reach blockchain should alert ops
        logger.critical(f"CRITICAL: Cannot record disease outbreak to blockchain: {e}")
        # In production, send alert to operations team
        # alert_ops_team(f"Blockchain unavailable during disease report: {e}")

        # Still return success (record is in database)
        # But mark for manual blockchain reconciliation
        # mark_for_blockchain_sync(disease_record)

    except BlockchainTransactionError as e:
        logger.critical(f"CRITICAL: Blockchain rejected disease outbreak: {e}")
        # This is likely a chaincode error - needs investigation
        # alert_developers(f"Chaincode error in disease reporting: {e}")

    return {
        "batch_id": str(batch_id),
        "disease_type": disease_type,
        "affected_count": affected_count,
        "status": "reported"
    }

# ==============================================================================

# Example 5: Testing Pattern

# ==============================================================================

"""
Unit Test Example:

from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_record_compliance_event(): # Mock the blockchain service
mock_blockchain = AsyncMock()
mock_blockchain.submit_transaction = AsyncMock(
return_value='{"status":"ok","tx_id":"abc123"}'
)

    # Patch the service initialization
    with patch(
        'app.services.blockchain_service.initialize_blockchain_service',
        return_value=mock_blockchain
    ):
        response = await record_compliance_event(
            event_data=ComplianceEventCreate(...),
            current_user=mock_user,
            db=mock_db
        )

    # Verify blockchain was called with correct arguments
    mock_blockchain.submit_transaction.assert_called_once_with(
        "RecordFarmerComplianceEvent",
        "farmer-uuid",
        "FOOD_SAFETY",
        "PASSED",
        ""
    )

    # Verify API response is successful
    assert response["status"] == "success"

@pytest.mark.asyncio
async def test_compliance_event_api_succeeds_if_blockchain_fails(): # Mock blockchain to fail
mock_blockchain = AsyncMock()
mock_blockchain.submit_transaction = AsyncMock(
side_effect=BlockchainConnectionError("Peer unavailable")
)

    with patch(
        'app.services.blockchain_service.initialize_blockchain_service',
        return_value=mock_blockchain
    ):
        response = await record_compliance_event(
            event_data=ComplianceEventCreate(...),
            current_user=mock_user,
            db=mock_db
        )

    # API should still return success
    assert response["status"] == "success"
    # Blockchain failure should not crash the endpoint

"""
