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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import Batch, BatchStatus, Product
from app.schemas.domain_schemas import BatchCreate, BatchUpdate, BatchResponse

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_data: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new batch for a specific product"""
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
        notes=batch_data.notes
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    return batch


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get batch details by ID"""
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
    db: Session = Depends(get_db)
):
    """Update batch details"""
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
    db: Session = Depends(get_db)
):
    """Archive or close a batch"""
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

    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "status": batch.status.value,
        "message": "Batch archived successfully"
    }
