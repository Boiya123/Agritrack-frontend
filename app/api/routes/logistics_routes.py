# Click dropdown on line 2 for briefing about the file
"""
Handles movement and cold chain of batches.

What goes here:

- Transport manifest creation

- Vehicle and driver assignment

- Departure and arrival logs

- Temperature monitoring

- Chain of custody tracking

What must NOT go here:

- Processing data

- Vaccination

- Regulatory approvals

- QR generation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import Transport, TemperatureLog, Batch
from app.schemas.domain_schemas import (
    TransportCreate, TransportUpdate, TransportResponse,
    TemperatureLogCreate, TemperatureLogResponse
)
# from app.services.blockchain_service import (
#     emit_custody_transfer,
#     emit_cold_chain_violation,
#     EventSeverity
# )

router = APIRouter(prefix="/logistics", tags=["logistics"])


@router.post("/transports", response_model=TransportResponse, status_code=status.HTTP_201_CREATED)
async def create_transport(
    transport_data: TransportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a transport manifest for a batch"""
    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == transport_data.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Only supplier, farmer, or admin can create transport
    if current_user.role not in [UserRole.FARMER, UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create transport"
        )

    transport = Transport(
        batch_id=transport_data.batch_id,
        from_party_id=current_user.id,
        to_party_id=transport_data.to_party_id,
        vehicle_id=transport_data.vehicle_id,
        driver_name=transport_data.driver_name,
        departure_time=transport_data.departure_time,
        origin_location=transport_data.origin_location,
        destination_location=transport_data.destination_location,
        temperature_monitored=transport_data.temperature_monitored,
        status="in_transit",
        notes=transport_data.notes
    )

    db.add(transport)
    db.commit()
    db.refresh(transport)

    return transport


@router.get("/transports/{transport_id}", response_model=TransportResponse)
async def get_transport(
    transport_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transport details"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    return transport


@router.get("/batches/{batch_id}/transports", response_model=list[TransportResponse])
async def get_batch_transports(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all transports for a batch"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    transports = (
        db.query(Transport)
        .filter(Transport.batch_id == batch_id)
        .order_by(Transport.departure_time.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transports


@router.put("/transports/{transport_id}", response_model=TransportResponse)
async def update_transport(
    transport_id: UUID,
    transport_data: TransportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update transport (arrival, status)"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    # Only from_party or admin can update
    if current_user.id != transport.from_party_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update transports you initiated"
        )

    if transport_data.arrival_time:
        transport.arrival_time = transport_data.arrival_time
        transport.status = "arrived"
    if transport_data.status:
        transport.status = transport_data.status
    if transport_data.notes is not None:
        transport.notes = transport_data.notes

    db.commit()
    db.refresh(transport)

    # Emit blockchain event on arrival
    if transport.arrival_time and transport.status == "arrived":
        await emit_custody_transfer(
            batch_id=transport.batch_id,
            from_party_id=transport.from_party_id,
            to_party_id=transport.to_party_id,
            from_party_role="FARMER",  # TODO: get from user role
            to_party_role="SUPPLIER",  # TODO: get from user role
            transport_id=transport.id
        )

    return transport


@router.post("/transports/{transport_id}/mark-completed")
async def mark_transport_completed(
    transport_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark transport as completed"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    # Only to_party or admin can mark completed
    if current_user.id != transport.to_party_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark transports you received as completed"
        )

    transport.status = "completed"
    db.commit()
    db.refresh(transport)

    return {
        "id": transport.id,
        "status": transport.status,
        "message": "Transport marked as completed"
    }


# Temperature Monitoring

@router.post("/temperature-logs", response_model=TemperatureLogResponse, status_code=status.HTTP_201_CREATED)
async def record_temperature(
    temp_data: TemperatureLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record temperature reading during transport"""
    transport = db.query(Transport).filter(Transport.id == temp_data.transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    if not transport.temperature_monitored:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature monitoring not enabled for this transport"
        )

    # Check if temperature is within acceptable range (e.g., 2-8°C for cold chain)
    is_violation = temp_data.temperature < 2 or temp_data.temperature > 8

    temp_log = TemperatureLog(
        transport_id=temp_data.transport_id,
        temperature=temp_data.temperature,
        timestamp=temp_data.timestamp,
        location=temp_data.location,
        is_violation=is_violation
    )

    db.add(temp_log)
    db.commit()
    db.refresh(temp_log)

    # Emit blockchain event if violation
    if is_violation:
        batch = db.query(Batch).filter(Batch.id == transport.batch_id).first()
        await emit_cold_chain_violation(
            batch_id=transport.batch_id,
            transport_id=transport.id,
            violation_type="temperature_out_of_range",
            temperature_readings=[temp_data.temperature],
            location=temp_data.location or "unknown"
        )

    return temp_log


@router.get("/transports/{transport_id}/temperature-logs", response_model=list[TemperatureLogResponse])
async def get_transport_temperatures(
    transport_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all temperature readings for a transport"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    temps = (
        db.query(TemperatureLog)
        .filter(TemperatureLog.transport_id == transport_id)
        .order_by(TemperatureLog.timestamp.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return temps


@router.get("/transports/{transport_id}/temperature-violations")
async def get_temperature_violations(
    transport_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get temperature violations for a transport"""
    transport = db.query(Transport).filter(Transport.id == transport_id).first()
    if not transport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transport not found"
        )

    violations = (
        db.query(TemperatureLog)
        .filter(
            TemperatureLog.transport_id == transport_id,
            TemperatureLog.is_violation == True
        )
        .all()
    )

    return {
        "transport_id": transport_id,
        "violation_count": len(violations),
        "violations": [
            {
                "id": v.id,
                "temperature": v.temperature,
                "timestamp": v.timestamp,
                "location": v.location
            }
            for v in violations
        ]
    }
