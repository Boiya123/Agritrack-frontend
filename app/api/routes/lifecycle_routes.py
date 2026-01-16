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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import LifecycleEvent, LifecycleEventType, Batch
from app.schemas.domain_schemas import LifecycleEventCreate, LifecycleEventResponse
# from app.services.blockchain_service import (
#     emit_disease_outbreak,
#     emit_mortality_threshold_exceeded,
#     EventSeverity
# )

router = APIRouter(prefix="/lifecycle", tags=["lifecycle"])


@router.post("", response_model=LifecycleEventResponse, status_code=status.HTTP_201_CREATED)
async def record_lifecycle_event(
    event_data: LifecycleEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a lifecycle event for a batch (vaccination, medication, mortality, etc.)"""
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
        metadata=event_data.metadata
    )

    db.add(lifecycle_event)
    db.commit()
    db.refresh(lifecycle_event)

    # Emit blockchain event for critical events
    if event_data.event_type.upper() in ["MORTALITY", "HATCH", "VACCINATION"]:
        await emit_lifecycle_blockchain_event(
            event_type=event_data.event_type.upper(),
            batch_id=event_data.batch_id,
            quantity=event_data.quantity_affected,
            description=event_data.description,
            db=db
        )

    return lifecycle_event


@router.get("/batches/{batch_id}/events", response_model=list[LifecycleEventResponse])
async def get_batch_lifecycle_events(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all lifecycle events for a batch"""
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
    """Get specific lifecycle event details"""
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
    db: Session = Depends(get_db)
):
    """Record vaccination event for a batch"""
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
        event_date=__import__('datetime').datetime.now(),
        quantity_affected=quantity_vaccinated,
        metadata=f'{{"vaccine_type": "{vaccine_type}"}}'
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "quantity_vaccinated": quantity_vaccinated,
        "vaccine_type": vaccine_type,
        "message": "Vaccination recorded successfully"
    }


@router.post("/record-medication")
async def record_medication(
    batch_id: UUID,
    medication_name: str,
    dosage: str,
    quantity_treated: int,
    current_user: User = Depends(get_current_user),
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
        event_date=__import__('datetime').datetime.now(),
        quantity_affected=quantity_treated,
        metadata=f'{{"medication": "{medication_name}", "dosage": "{dosage}"}}'
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "medication_name": medication_name,
        "dosage": dosage,
        "quantity_treated": quantity_treated,
        "message": "Medication recorded successfully"
    }


@router.post("/record-mortality")
async def record_mortality(
    batch_id: UUID,
    mortality_count: int,
    cause: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record mortality event (triggers blockchain event if threshold exceeded)"""
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
        event_date=__import__('datetime').datetime.now(),
        quantity_affected=mortality_count,
        metadata=f'{{"cause": "{cause}"}}'
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    # Check if mortality exceeds threshold (5% is example threshold)
    mortality_rate = (mortality_count / batch.quantity) * 100
    if mortality_rate > 5:
        # Emit blockchain event for abnormal mortality
        await emit_mortality_threshold_exceeded(
            batch_id=batch_id,
            farmer_id=batch.farmer_id,
            mortality_count=mortality_count,
            mortality_rate=mortality_rate,
            threshold=5.0
        )

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "mortality_count": mortality_count,
        "mortality_rate_percentage": round(mortality_rate, 2),
        "cause": cause,
        "message": "Mortality recorded successfully"
    }


@router.post("/record-weight")
async def record_weight_measurement(
    batch_id: UUID,
    average_weight_kg: float,
    sample_count: int,
    current_user: User = Depends(get_current_user),
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
        event_date=__import__('datetime').datetime.now(),
        metadata=f'{{"average_weight_kg": {average_weight_kg}, "sample_count": {sample_count}}}'
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "batch_id": batch_id,
        "event_type": event.event_type.value,
        "average_weight_kg": average_weight_kg,
        "sample_count": sample_count,
        "message": "Weight measurement recorded successfully"
    }


async def emit_lifecycle_blockchain_event(
    event_type: str,
    batch_id: UUID,
    quantity: int,
    description: str,
    db: Session
):
    """Emit blockchain event for critical lifecycle events"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        return

    # For now, just log - blockchain integration to follow
    # This is where we'd call blockchain_service functions
    pass
