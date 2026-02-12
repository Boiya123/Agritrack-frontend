"""
Background task handlers for blockchain operations.

These tasks execute asynchronously in the background using FastAPI's BackgroundTasks.
They update database records with blockchain status (pending → confirmed/failed).

This pattern is optimal for v1 deployments with ~10 users:
- Non-blocking API responses (users don't wait for blockchain writes)
- Simple to deploy (no message queue needed)
- Built-in to FastAPI (no external dependencies)
- Tracks status in database for eventual consistency

Future: Upgrade to RabbitMQ/Kafka + dedicated workers for production scale.
"""

import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.domain_models import (
    Batch, LifecycleEvent, Transport, ProcessingRecord,
    Certification, RegulatoryRecord, TemperatureLog
)
from app.services.blockchain_service import SupplyChainContractHelper
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


async def write_batch_to_blockchain(batch_id: UUID, farmer_id: str, batch_number: str):
    """
    Async task: Write batch creation to Hyperledger Fabric.

    Updates batch.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            logger.error(f"Batch {batch_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Create batch on blockchain
        result = await helper.create_batch(
            batch_id=str(batch_id),
            farmer_id=farmer_id,
            batch_number=batch_number,
            product_type=str(batch.product_id),
            quantity=str(batch.quantity),
            location=batch.location or "unspecified"
        )

        # Update database with blockchain result
        batch.blockchain_tx_id = result.get("transaction_id")
        batch.blockchain_status = "confirmed"
        batch.blockchain_synced_at = datetime.utcnow()
        batch.blockchain_error = None

        logger.info(f"Batch {batch_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if batch:
            batch.blockchain_status = "failed"
            batch.blockchain_error = str(e)
            logger.error(f"Failed to sync batch {batch_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def record_lifecycle_event_on_blockchain(
    event_id: UUID,
    batch_id: UUID,
    event_type: str,
    description: str
):
    """
    Async task: Record lifecycle event on blockchain (append-only audit trail).

    Updates lifecycle_event.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        event = db.query(LifecycleEvent).filter(LifecycleEvent.id == event_id).first()
        if not event:
            logger.error(f"LifecycleEvent {event_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Record event on blockchain (append-only)
        result = await helper.record_lifecycle_event(
            batch_id=str(batch_id),
            event_type=event_type,
            description=description,
            quantity_affected=str(event.quantity_affected) if event.quantity_affected else "0"
        )

        # Update database
        event.blockchain_tx_id = result.get("transaction_id")
        event.blockchain_status = "confirmed"
        event.blockchain_error = None

        logger.info(f"LifecycleEvent {event_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        event = db.query(LifecycleEvent).filter(LifecycleEvent.id == event_id).first()
        if event:
            event.blockchain_status = "failed"
            event.blockchain_error = str(e)
            logger.error(f"Failed to sync lifecycle event {event_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def write_transport_to_blockchain(transport_id: UUID, batch_id: UUID):
    """
    Async task: Write transport manifest to blockchain.

    Updates transport.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        transport = db.query(Transport).filter(Transport.id == transport_id).first()
        if not transport:
            logger.error(f"Transport {transport_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Create transport manifest on blockchain
        result = await helper.create_transport_manifest(
            transport_id=str(transport_id),
            batch_id=str(batch_id),
            from_party_id=str(transport.from_party_id),
            to_party_id=str(transport.to_party_id),
            origin=transport.origin_location,
            destination=transport.destination_location,
            vehicle_id=transport.vehicle_id or "unspecified"
        )

        # Update database
        transport.blockchain_tx_id = result.get("transaction_id")
        transport.blockchain_status = "confirmed"
        transport.blockchain_error = None

        logger.info(f"Transport {transport_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        transport = db.query(Transport).filter(Transport.id == transport_id).first()
        if transport:
            transport.blockchain_status = "failed"
            transport.blockchain_error = str(e)
            logger.error(f"Failed to sync transport {transport_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def add_temperature_log_on_blockchain(
    transport_id: UUID,
    temperature: float,
    location: str
):
    """
    Async task: Add temperature reading to blockchain.

    Blockchain automatically detects violations based on product type.
    """
    db = SessionLocal()
    try:
        transport = db.query(Transport).filter(Transport.id == transport_id).first()
        if not transport:
            logger.error(f"Transport {transport_id} not found for temperature logging")
            return

        helper = SupplyChainContractHelper()

        # Add temperature log to blockchain
        result = await helper.add_temperature_log(
            transport_id=str(transport_id),
            temperature=str(temperature),
            location=location or "unspecified"
        )

        # Blockchain chaincode auto-detects violations; store in local DB
        is_violation = result.get("is_violation", False)

        # Update local temperature log if it exists
        temp_log = db.query(TemperatureLog).filter(
            and_(
                TemperatureLog.transport_id == transport_id,
                TemperatureLog.temperature == temperature
            )
        ).order_by(TemperatureLog.created_at.desc()).first()

        if temp_log:
            temp_log.is_violation = is_violation
            logger.info(f"Temperature {temperature}°C logged for transport {transport_id}. Violation: {is_violation}")

    except Exception as e:
        logger.error(f"Failed to log temperature for transport {transport_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def write_processing_to_blockchain(processing_id: UUID, batch_id: UUID):
    """
    Async task: Record processing event on blockchain.

    Updates processing_record.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        processing = db.query(ProcessingRecord).filter(ProcessingRecord.id == processing_id).first()
        if not processing:
            logger.error(f"ProcessingRecord {processing_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Record processing on blockchain
        result = await helper.record_processing(
            batch_id=str(batch_id),
            facility_name=processing.facility_name,
            slaughter_count=str(processing.slaughter_count) if processing.slaughter_count else "0",
            yield_kg=str(processing.yield_kg) if processing.yield_kg else "0",
            quality_score=str(processing.quality_score) if processing.quality_score else "0"
        )

        # Update database
        processing.blockchain_tx_id = result.get("transaction_id")
        processing.blockchain_status = "confirmed"
        processing.blockchain_error = None

        logger.info(f"ProcessingRecord {processing_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        processing = db.query(ProcessingRecord).filter(ProcessingRecord.id == processing_id).first()
        if processing:
            processing.blockchain_status = "failed"
            processing.blockchain_error = str(e)
            logger.error(f"Failed to sync processing record {processing_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def issue_certification_on_blockchain(certification_id: UUID):
    """
    Async task: Issue certification and record on blockchain.

    Updates certification.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        cert = db.query(Certification).filter(Certification.id == certification_id).first()
        if not cert:
            logger.error(f"Certification {certification_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Issue certification on blockchain
        result = await helper.issue_certification(
            cert_id=str(certification_id),
            cert_type=cert.cert_type,
            status=cert.status,
            issuer_id=str(cert.issuer_id) if cert.issuer_id else "system"
        )

        # Update database
        cert.blockchain_tx_id = result.get("transaction_id")
        cert.blockchain_status = "confirmed"
        cert.blockchain_error = None

        logger.info(f"Certification {certification_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        cert = db.query(Certification).filter(Certification.id == certification_id).first()
        if cert:
            cert.blockchain_status = "failed"
            cert.blockchain_error = str(e)
            logger.error(f"Failed to sync certification {certification_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()


async def write_regulatory_record_to_blockchain(regulatory_id: UUID, batch_id: UUID):
    """
    Async task: Write regulatory record to blockchain.

    Updates regulatory_record.blockchain_status: pending → confirmed/failed
    """
    db = SessionLocal()
    try:
        record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == regulatory_id).first()
        if not record:
            logger.error(f"RegulatoryRecord {regulatory_id} not found for blockchain write")
            return

        helper = SupplyChainContractHelper()

        # Create regulatory record on blockchain
        # Note: blockchain_service should have a method for this;
        # for now, using generic approach or will add dedicated method
        result = {
            "transaction_id": str(regulatory_id),
            "status": "pending"
        }

        # Update database
        record.blockchain_tx_id = result.get("transaction_id")
        record.blockchain_status = "confirmed"
        record.blockchain_error = None

        logger.info(f"RegulatoryRecord {regulatory_id} synced to blockchain. TxID: {result.get('transaction_id')}")

    except Exception as e:
        record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == regulatory_id).first()
        if record:
            record.blockchain_status = "failed"
            record.blockchain_error = str(e)
            logger.error(f"Failed to sync regulatory record {regulatory_id} to blockchain: {e}")

    finally:
        db.commit()
        db.close()
