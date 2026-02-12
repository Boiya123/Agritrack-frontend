# Click dropdown on line 2 for briefing about the file
"""
Handles everything that happens to a batch over time.

    This is the MOST IMPORTANT audit trail route.

What goes here:

- Vaccination records

- Medication records

- Weight measurements

- Feeding logs

- Mortality reports

- Hatch events

- Environmental logs

What must NOT go here:

- Batch creation

- Transport manifests

- Processing and slaughter

- Regulatory approvals
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import LifecycleEvent, LifecycleEventType, Batch
from app.schemas.domain_schemas import LifecycleEventCreate, LifecycleEventResponse
from app.services.blockchain_tasks import record_lifecycle_event_on_blockchain

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lifecycle", tags=["lifecycle"])


@router.post("", response_model=LifecycleEventResponse, status_code=status.HTTP_201_CREATED)
async def record_lifecycle_event(
    event_data: LifecycleEventCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Record a lifecycle event for a batch (vaccination, medication, mortality, etc.)

    Lifecycle events form an APPEND-ONLY audit trail on the blockchain.
    This creates an immutable record of everything that happens to a batch:
    - Vaccinations (with vaccine type and quantity)
    - Medications (dosage and quantity treated)
    - Mortality reports (with cause)
    - Weight measurements
    - Feeding logs
    - Environmental conditions

    Each event is queued asynchronously for blockchain synchronization.
    Status: pending → confirmed
    """
    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == event_data.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Farmers can record events for their own batches, others need specific role
    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only record events for your own batches"
        )

    # Create lifecycle event
    lifecycle_event = LifecycleEvent(
        batch_id=event_data.batch_id,
        event_type=LifecycleEventType[event_data.event_type.upper()],
        description=event_data.description,
        recorded_by=current_user.id,
        event_date=event_data.event_date,
        quantity_affected=event_data.quantity_affected,
        event_metadata=event_data.metadata,
        blockchain_status="pending"
    )

    db.add(lifecycle_event)
    db.commit()
    db.refresh(lifecycle_event)

    # Queue blockchain write asynchronously (append-only)
    background_tasks.add_task(
        record_lifecycle_event_on_blockchain,
        event_id=lifecycle_event.id,
        batch_id=event_data.batch_id,
        event_type=event_data.event_type.upper(),
        description=event_data.description
    )

    logger.info(f"LifecycleEvent {lifecycle_event.id} recorded for batch {event_data.batch_id}. Blockchain sync queued.")

    return lifecycle_event


@router.get("/batches/{batch_id}/events", response_model=list[LifecycleEventResponse])
async def get_batch_lifecycle_events(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all lifecycle events for a batch (append-only audit trail)

    Returns events in reverse chronological order (newest first).
    Each event shows blockchain_status tracking.
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    events = (
        db.query(LifecycleEvent)
        .filter(LifecycleEvent.batch_id == batch_id)
        .order_by(LifecycleEvent.event_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return events


@router.get("/{event_id}", response_model=LifecycleEventResponse)
async def get_lifecycle_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific lifecycle event details with blockchain status"""
    event = db.query(LifecycleEvent).filter(LifecycleEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    return event


@router.post("/record-vaccination")
async def record_vaccination(
    batch_id: UUID,
    vaccine_type: str,
    quantity_vaccinated: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Record vaccination event for a batch

    Vaccination records are critical for traceability and are appended
    to the immutable blockchain record.
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only record events for your own batches"
        )

    event = LifecycleEvent(
        batch_id=batch_id,
        event_type=LifecycleEventType.VACCINATION,
        description=f"Vaccinated {quantity_vaccinated} with {vaccine_type}",
        recorded_by=current_user.id,
        event_date=datetime.utcnow(),
        quantity_affected=quantity_vaccinated,
        event_metadata=f'{{"vaccine_type": "{vaccine_type}"}}',
        blockchain_status="pending"
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # Queue blockchain write
    background_tasks.add_task(
        record_lifecycle_event_on_blockchain,
        event_id=event.id,
        batch_id=batch_id,
        event_type="VACCINATION",
        description=event.description
    )

    logger.info(f"Vaccination recorded for batch {batch_id}. Blockchain sync queued.")

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "quantity_vaccinated": quantity_vaccinated,
        "vaccine_type": vaccine_type,
        "blockchain_status": event.blockchain_status,
        "message": "Vaccination recorded successfully"
    }


@router.post("/record-medication")
async def record_medication(
    batch_id: UUID,
    medication_name: str,
    dosage: str,
    quantity_treated: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Record medication event for a batch"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only record events for your own batches"
        )

    event = LifecycleEvent(
        batch_id=batch_id,
        event_type=LifecycleEventType.MEDICATION,
        description=f"Administered {medication_name} ({dosage}) to {quantity_treated}",
        recorded_by=current_user.id,
        event_date=datetime.utcnow(),
        quantity_affected=quantity_treated,
        event_metadata=f'{{"medication": "{medication_name}", "dosage": "{dosage}"}}',
        blockchain_status="pending"
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # Queue blockchain write
    background_tasks.add_task(
        record_lifecycle_event_on_blockchain,
        event_id=event.id,
        batch_id=batch_id,
        event_type="MEDICATION",
        description=event.description
    )

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "medication_name": medication_name,
        "dosage": dosage,
        "quantity_treated": quantity_treated,
        "blockchain_status": event.blockchain_status,
        "message": "Medication recorded successfully"
    }


@router.post("/record-mortality")
async def record_mortality(
    batch_id: UUID,
    mortality_count: int,
    cause: str,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Record mortality event (triggers blockchain event if threshold exceeded)

    Mortality is a critical compliance indicator. High mortality rates
    trigger automatic blockchain records that are visible to regulators.
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only record events for your own batches"
        )

    event = LifecycleEvent(
        batch_id=batch_id,
        event_type=LifecycleEventType.MORTALITY,
        description=f"Mortality reported: {mortality_count} units. Cause: {cause}",
        recorded_by=current_user.id,
        event_date=datetime.utcnow(),
        quantity_affected=mortality_count,
        event_metadata=f'{{"cause": "{cause}"}}',
        blockchain_status="pending"
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # Check if mortality exceeds threshold (5% is example threshold)
    mortality_rate = (mortality_count / batch.quantity) * 100 if batch.quantity > 0 else 0

    # Queue blockchain write
    background_tasks.add_task(
        record_lifecycle_event_on_blockchain,
        event_id=event.id,
        batch_id=batch_id,
        event_type="MORTALITY",
        description=event.description
    )

    if mortality_rate > 5:
        logger.warning(f"High mortality rate ({mortality_rate}%) detected for batch {batch_id}")

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "mortality_count": mortality_count,
        "mortality_rate_percentage": round(mortality_rate, 2),
        "cause": cause,
        "blockchain_status": event.blockchain_status,
        "message": "Mortality recorded successfully"
    }


@router.post("/record-weight")
async def record_weight_measurement(
    batch_id: UUID,
    average_weight_kg: float,
    sample_count: int,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Record weight measurement event"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only record events for your own batches"
        )

    event = LifecycleEvent(
        batch_id=batch_id,
        event_type=LifecycleEventType.WEIGHT_MEASUREMENT,
        description=f"Weight measurement: {average_weight_kg}kg (sample: {sample_count})",
        recorded_by=current_user.id,
        event_date=datetime.utcnow(),
        event_metadata=f'{{"average_weight_kg": {average_weight_kg}, "sample_count": {sample_count}}}',
        blockchain_status="pending"
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # Queue blockchain write
    background_tasks.add_task(
        record_lifecycle_event_on_blockchain,
        event_id=event.id,
        batch_id=batch_id,
        event_type="WEIGHT_MEASUREMENT",
        description=event.description
    )

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "average_weight_kg": average_weight_kg,
        "sample_count": sample_count,
        "blockchain_status": event.blockchain_status,
        "message": "Weight measurement recorded successfully"
    }
