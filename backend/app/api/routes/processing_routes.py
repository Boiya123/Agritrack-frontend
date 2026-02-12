# Click dropdown on line 2 for briefing about the file
"""
Handles what happens when the batch is converted to product for consumption.

- What goes here

- Slaughter records

- Processing facility records

- Yield reports

- Quality checks

- Certifications like halal

What must NOT go here:

- Transport data

- Vaccination

- QR generation

- Regulatory approvals
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from datetime import datetime, timedelta

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import ProcessingRecord, Certification, Batch
from app.schemas.domain_schemas import (
    ProcessingRecordCreate, ProcessingRecordUpdate, ProcessingRecordResponse,
    CertificationCreate, CertificationUpdate, CertificationResponse
)
from app.services.blockchain_tasks import (
    write_processing_to_blockchain,
    issue_certification_on_blockchain
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/records", response_model=ProcessingRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_processing_record(
    record_data: ProcessingRecordCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create a processing facility record for a batch

    Processing records track the conversion of batches to final products:
    - Slaughter/harvest counts
    - Yield measurements
    - Quality assessments
    - Facility information

    Blockchain: Processing records are synced asynchronously for permanent
    traceability from production to final product delivery.
    """
    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == record_data.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Only supplier or admin can create processing records
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can create processing records"
        )

    processing_record = ProcessingRecord(
        batch_id=record_data.batch_id,
        processing_date=record_data.processing_date,
        facility_name=record_data.facility_name,
        slaughter_count=record_data.slaughter_count,
        yield_kg=record_data.yield_kg,
        quality_score=record_data.quality_score,
        notes=record_data.notes,
        blockchain_status="pending"
    )

    db.add(processing_record)
    db.commit()
    db.refresh(processing_record)

    # Queue blockchain write
    background_tasks.add_task(
        write_processing_to_blockchain,
        processing_id=processing_record.id,
        batch_id=record_data.batch_id
    )

    logger.info(f"ProcessingRecord {processing_record.id} created. Blockchain sync queued.")
    return processing_record


@router.get("/records/{record_id}", response_model=ProcessingRecordResponse)
async def get_processing_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing record details with blockchain status"""
    record = db.query(ProcessingRecord).filter(ProcessingRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing record not found"
        )

    return record


@router.get("/batches/{batch_id}/records", response_model=list[ProcessingRecordResponse])
async def get_batch_processing_records(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all processing records for a batch"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    records = (
        db.query(ProcessingRecord)
        .filter(ProcessingRecord.batch_id == batch_id)
        .order_by(ProcessingRecord.processing_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return records


@router.put("/records/{record_id}", response_model=ProcessingRecordResponse)
async def update_processing_record(
    record_id: UUID,
    record_data: ProcessingRecordUpdate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Update processing record (quality score, notes)"""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can update processing records"
        )

    record = db.query(ProcessingRecord).filter(ProcessingRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing record not found"
        )

    if record_data.quality_score is not None:
        record.quality_score = record_data.quality_score
        # Quality failures (score < 60) are logged
        if record_data.quality_score < 60:
            logger.warning(f"Low quality score ({record_data.quality_score}) for processing record {record_id}")

    if record_data.notes is not None:
        record.notes = record_data.notes

    db.commit()
    db.refresh(record)

    return record


# Certifications

@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_certification(
    cert_data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create a certification record for a processing record

    Certifications verify compliance with specific standards:
    - Halal certification
    - Organic certification
    - Food safety certifications
    - Traceability certifications

    Blockchain: Certifications are immutably recorded on blockchain
    to prevent forgery and maintain consumer trust.
    """
    # Verify processing record exists
    record = db.query(ProcessingRecord).filter(
        ProcessingRecord.id == cert_data.processing_record_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing record not found"
        )

    # Only supplier or admin can create certifications
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can create certifications"
        )

    certification = Certification(
        processing_record_id=cert_data.processing_record_id,
        cert_type=cert_data.cert_type,
        status="pending",
        notes=cert_data.notes,
        blockchain_status="pending"
    )

    db.add(certification)
    db.commit()
    db.refresh(certification)

    # Queue blockchain write
    background_tasks.add_task(
        issue_certification_on_blockchain,
        certification_id=certification.id
    )

    logger.info(f"Certification {certification.id} created. Blockchain sync queued.")
    return certification


@router.get("/certifications/{cert_id}", response_model=CertificationResponse)
async def get_certification(
    cert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get certification details with blockchain status"""
    cert = db.query(Certification).filter(Certification.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )

    return cert


@router.get("/records/{record_id}/certifications", response_model=list[CertificationResponse])
async def get_record_certifications(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certifications for a processing record"""
    record = db.query(ProcessingRecord).filter(ProcessingRecord.id == record_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing record not found"
        )

    certs = (
        db.query(Certification)
        .filter(Certification.processing_record_id == record_id)
        .order_by(Certification.created_at.desc())
        .all()
    )

    return certs


@router.put("/certifications/{cert_id}", response_model=CertificationResponse)
async def update_certification(
    cert_id: UUID,
    cert_data: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update certification status (approve/fail)"""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can update certifications"
        )

    cert = db.query(Certification).filter(Certification.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )

    cert.status = cert_data.status
    cert.issuer_id = current_user.id

    if cert_data.issued_date:
        cert.issued_date = cert_data.issued_date
    if cert_data.expiry_date:
        cert.expiry_date = cert_data.expiry_date
    if cert_data.notes:
        cert.notes = cert_data.notes

    db.commit()
    db.refresh(cert)

    return cert


@router.post("/certifications/{cert_id}/approve")
async def approve_certification(
    cert_id: UUID,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Approve a certification"""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can approve certifications"
        )

    cert = db.query(Certification).filter(Certification.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )

    cert.status = "approved"
    cert.issuer_id = current_user.id
    cert.issued_date = datetime.utcnow()
    cert.expiry_date = datetime.utcnow() + timedelta(days=365)  # 1 year validity

    db.commit()
    db.refresh(cert)

    logger.info(f"Certification {cert_id} approved")

    return {
        "id": cert.id,
        "cert_type": cert.cert_type,
        "status": cert.status,
        "issued_date": cert.issued_date,
        "expiry_date": cert.expiry_date,
        "message": "Certification approved successfully"
    }


@router.post("/certifications/{cert_id}/reject")
async def reject_certification(
    cert_id: UUID,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a certification"""
    if current_user.role not in [UserRole.SUPPLIER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only suppliers can reject certifications"
        )

    cert = db.query(Certification).filter(Certification.id == cert_id).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )

    cert.status = "failed"
    cert.issuer_id = current_user.id
    cert.notes = reason

    db.commit()
    db.refresh(cert)

    return {
        "id": cert.id,
        "cert_type": cert.cert_type,
        "status": cert.status,
        "rejection_reason": reason,
        "message": "Certification rejected"
    }
