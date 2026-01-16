# Click dropdown on line 2 for briefing about the file
"""
Handles legal, export, and government verification.

What goes here:

- Attach health certificates

- Export permits

- Regulator approvals

- Compliance rejection

- Audit flags

What must NOT go here:

- Batch creation

- Event creation

- Transport

- Processing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import RegulatoryRecord, Batch
from app.schemas.domain_schemas import (
    RegulatoryRecordCreate, RegulatoryRecordUpdate, RegulatoryRecordResponse
)
# from app.services.blockchain_service import (
#     emit_certification_failed,
#     emit_regulatory_violation,
#     EventSeverity
# )

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


@router.post("/records", response_model=RegulatoryRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_regulatory_record(
    record_data: RegulatoryRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a regulatory record (health cert, export permit, etc.)"""
    # Only regulators and admins can create regulatory records
    if current_user.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regulators can create regulatory records"
        )

    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == record_data.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    record = RegulatoryRecord(
        batch_id=record_data.batch_id,
        record_type=record_data.record_type,
        status="pending",
        regulator_id=current_user.id,
        details=record_data.details
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/records/{record_id}", response_model=RegulatoryRecordResponse)
async def get_regulatory_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get regulatory record details"""
    record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory record not found"
        )

    return record


@router.get("/batches/{batch_id}/records", response_model=list[RegulatoryRecordResponse])
async def get_batch_regulatory_records(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all regulatory records for a batch"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    records = (
        db.query(RegulatoryRecord)
        .filter(RegulatoryRecord.batch_id == batch_id)
        .order_by(RegulatoryRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return records


@router.put("/records/{record_id}", response_model=RegulatoryRecordResponse)
async def update_regulatory_record(
    record_id: UUID,
    record_data: RegulatoryRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update regulatory record status"""
    if current_user.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regulators can update regulatory records"
        )

    record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory record not found"
        )

    record.status = record_data.status

    if record_data.issued_date:
        record.issued_date = record_data.issued_date
    if record_data.expiry_date:
        record.expiry_date = record_data.expiry_date
    if record_data.rejection_reason:
        record.rejection_reason = record_data.rejection_reason
    if record_data.audit_flags:
        record.audit_flags = record_data.audit_flags

    db.commit()
    db.refresh(record)

    # Emit blockchain event if rejected
    if record.status == "rejected":
        batch = db.query(Batch).filter(Batch.id == record.batch_id).first()
        if batch:
            await emit_regulatory_violation(
                farmer_id=batch.farmer_id,
                violation_type=f"Regulatory_{record.record_type}_REJECTED",
                description=record.rejection_reason or f"{record.record_type} was rejected",
                regulator_id=current_user.id
            )

    return record


@router.post("/records/{record_id}/approve")
async def approve_regulatory_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a regulatory record"""
    if current_user.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regulators can approve regulatory records"
        )

    record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory record not found"
        )

    from datetime import datetime, timedelta

    record.status = "approved"
    record.issued_date = datetime.now()

    # Set expiry based on record type
    if "cert" in record.record_type.lower():
        record.expiry_date = datetime.now() + timedelta(days=365)
    elif "permit" in record.record_type.lower():
        record.expiry_date = datetime.now() + timedelta(days=30)

    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "record_type": record.record_type,
        "status": record.status,
        "issued_date": record.issued_date,
        "expiry_date": record.expiry_date,
        "message": f"{record.record_type} approved successfully"
    }


@router.post("/records/{record_id}/reject")
async def reject_regulatory_record(
    record_id: UUID,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a regulatory record (triggers blockchain event)"""
    if current_user.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regulators can reject regulatory records"
        )

    record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory record not found"
        )

    record.status = "rejected"
    record.rejection_reason = reason

    db.commit()
    db.refresh(record)

    # Emit blockchain event for rejection
    batch = db.query(Batch).filter(Batch.id == record.batch_id).first()
    if batch:
        await emit_regulatory_violation(
            farmer_id=batch.farmer_id,
            violation_type=f"{record.record_type}_REJECTED",
            description=reason,
            regulator_id=current_user.id
        )

    return {
        "id": record.id,
        "record_type": record.record_type,
        "status": record.status,
        "rejection_reason": reason,
        "message": f"{record.record_type} rejected"
    }


@router.post("/records/{record_id}/add-audit-flag")
async def add_audit_flag(
    record_id: UUID,
    flag: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add an audit flag to a regulatory record"""
    if current_user.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regulators can add audit flags"
        )

    record = db.query(RegulatoryRecord).filter(RegulatoryRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory record not found"
        )

    import json

    # Parse existing flags or create new list
    flags = []
    if record.audit_flags:
        try:
            flags = json.loads(record.audit_flags)
        except:
            flags = []

    if flag not in flags:
        flags.append(flag)
        record.audit_flags = json.dumps(flags)

    db.commit()
    db.refresh(record)

    # Emit blockchain event for compliance issue
    batch = db.query(Batch).filter(Batch.id == record.batch_id).first()
    if batch:
        await emit_regulatory_violation(
            farmer_id=batch.farmer_id,
            violation_type="AUDIT_FLAG",
            description=f"Audit flag added: {flag}",
            regulator_id=current_user.id
        )

    return {
        "id": record.id,
        "record_type": record.record_type,
        "audit_flags": flags,
        "message": "Audit flag added successfully"
    }


@router.get("/farmers/{farmer_id}/compliance-status")
async def get_farmer_compliance_status(
    farmer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get compliance status for a farmer (all regulatory records)"""
    # Get all batches for farmer
    batches = db.query(Batch).filter(Batch.farmer_id == farmer_id).all()
    batch_ids = [b.id for b in batches]

    if not batch_ids:
        return {
            "farmer_id": farmer_id,
            "total_batches": 0,
            "compliance_records": []
        }

    # Get all regulatory records for farmer's batches
    records = (
        db.query(RegulatoryRecord)
        .filter(RegulatoryRecord.batch_id.in_(batch_ids))
        .order_by(RegulatoryRecord.created_at.desc())
        .all()
    )

    # Summarize status
    approved = len([r for r in records if r.status == "approved"])
    rejected = len([r for r in records if r.status == "rejected"])
    pending = len([r for r in records if r.status == "pending"])

    return {
        "farmer_id": farmer_id,
        "total_batches": len(batches),
        "compliance_summary": {
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "total": len(records)
        },
        "compliance_records": [
            {
                "id": r.id,
                "batch_id": r.batch_id,
                "record_type": r.record_type,
                "status": r.status,
                "issued_date": r.issued_date,
                "expiry_date": r.expiry_date,
                "rejection_reason": r.rejection_reason,
                "audit_flags": r.audit_flags
            }
            for r in records
        ]
    }
