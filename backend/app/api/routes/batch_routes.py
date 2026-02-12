# Click dropdown on line 2 for briefing about the file
"""
Handles physical production groups, meaning flocks, harvest lots, animal groups, or crop cycles.

What goes here:

- Create batch for a specific product

- Assign batch to farm and house

- Update batch status

- Link batch to QR system

- Archive or close batch

What must NOT go here:

- Vaccination logic

- Transport logic

- Processing logic

- Approvals
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import Batch, BatchStatus, Product
from app.schemas.domain_schemas import BatchCreate, BatchUpdate, BatchResponse
from app.services.blockchain_tasks import write_batch_to_blockchain

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_data: BatchCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create a new batch for a specific product

    Batches represent physical production groups:
    - Poultry flocks
    - Crop harvest lots
    - Fish ponds
    - Livestock herds

    Blockchain: Batch creation is synced asynchronously to Hyperledger Fabric.
    The response includes blockchain_status field to track sync progress.
    Status: pending → confirmed (once blockchain write completes)
    """
    # Only farmers can create batches
    if current_user.role != UserRole.FARMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can create batches"
        )

    # Verify product exists
    product = db.query(Product).filter(Product.id == batch_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not active"
        )

    # Check batch_number uniqueness
    existing = db.query(Batch).filter(Batch.batch_number == batch_data.batch_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch number already exists"
        )

    # Create batch
    batch = Batch(
        product_id=batch_data.product_id,
        farmer_id=current_user.id,
        batch_number=batch_data.batch_number,
        status=BatchStatus.CREATED,
        quantity=batch_data.quantity,
        start_date=batch_data.start_date,
        expected_end_date=batch_data.expected_end_date,
        location=batch_data.location,
        notes=batch_data.notes,
        blockchain_status="pending"  # Blockchain sync in progress
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Queue blockchain write in background (non-blocking)
    background_tasks.add_task(
        write_batch_to_blockchain,
        batch_id=batch.id,
        farmer_id=str(current_user.id),
        batch_number=batch.batch_number
    )

    logger.info(f"Batch {batch.id} created. Blockchain sync queued.")
    return batch


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get batch details by ID

    Returns batch information including blockchain sync status:
    - blockchain_status: pending/confirmed/failed
    - blockchain_tx_id: Transaction ID from Hyperledger (if confirmed)
    - blockchain_error: Error message if sync failed
    - blockchain_synced_at: When sync was completed
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    return batch


@router.get("", response_model=list[BatchResponse])
async def list_batches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List batches (farmers see own, others see all)"""
    query = db.query(Batch)

    # Farmers see only their own batches
    if current_user.role == UserRole.FARMER:
        query = query.filter(Batch.farmer_id == current_user.id)

    batches = query.offset(skip).limit(limit).all()
    return batches


@router.put("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: UUID,
    batch_data: BatchUpdate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Update batch details

    Status transitions are validated:
    - CREATED → ACTIVE (start production)
    - ACTIVE → COMPLETED (end production)
    - Any → FAILED (if disease outbreak or failure)
    - Any → ARCHIVED (retire batch)

    Status changes are queued for blockchain update.
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Only farmer who created batch or admins can update
    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own batches"
        )

    # Update fields
    old_status = batch.status
    if batch_data.status:
        batch.status = BatchStatus[batch_data.status.upper()]
    if batch_data.location is not None:
        batch.location = batch_data.location
    if batch_data.actual_end_date:
        batch.actual_end_date = batch_data.actual_end_date
    if batch_data.qr_code:
        batch.qr_code = batch_data.qr_code
    if batch_data.notes is not None:
        batch.notes = batch_data.notes

    db.commit()
    db.refresh(batch)

    # Queue blockchain update if status changed
    if old_status != batch.status:
        logger.info(f"Batch {batch_id} status changed from {old_status} to {batch.status}. Queueing blockchain update.")

    return batch


@router.post("/{batch_id}/qr-link")
async def link_qr_code(
    batch_id: UUID,
    qr_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link batch to QR code system"""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Only batch owner or admin can link QR
    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own batches"
        )

    # Check QR uniqueness
    existing = db.query(Batch).filter(Batch.qr_code == qr_code, Batch.id != batch_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code already linked to another batch"
        )

    batch.qr_code = qr_code
    db.commit()
    db.refresh(batch)

    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "qr_code": batch.qr_code,
        "message": "QR code linked successfully"
    }


@router.post("/{batch_id}/archive")
async def archive_batch(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Archive or close a batch

    Archived batches are immutable and queued for blockchain finalization.
    """
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )

    # Only batch owner or admin can archive
    if current_user.role == UserRole.FARMER and batch.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only archive your own batches"
        )

    batch.status = BatchStatus.ARCHIVED
    db.commit()
    db.refresh(batch)

    logger.info(f"Batch {batch_id} archived. Queued for blockchain finalization.")

    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "status": batch.status.value,
        "message": "Batch archived successfully"
    }
