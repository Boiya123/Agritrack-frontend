# Click dropdown on line 2 for briefing about the file
"""
Handles what type of agricultural product exists in the system. Poultry is just one entry here.

What goes here:

- Create a product type like poultry, rice, corn, fish

- List all supported products

- Enable or disable a product type

- Attach product level rules

What must NOT go here:

- Batch creation

- Farm ownership

- Vaccination and lifecycle data
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User, UserRole
from app.models.domain_models import Product
from app.schemas.domain_schemas import ProductCreate, ProductUpdate, ProductResponse
from app.services.blockchain_service import SupplyChainContractHelper
from app.services.blockchain_tasks import write_batch_to_blockchain

router = APIRouter(prefix="/products", tags=["products"])


async def _create_product_blockchain(product_id: str, product_name: str):
    """Background task: Create product on blockchain"""
    try:
        helper = SupplyChainContractHelper()
        await helper.create_product(
            product_id=product_id,
            product_name=product_name,
            product_type=product_name
        )
    except Exception as e:
        logger.error(f"Failed to create product {product_id} on blockchain: {e}")


import logging
logger = logging.getLogger(__name__)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Create a new product type (admin only)

    Product types represent agricultural products that can be tracked:
    - Poultry (chicken, duck, turkey)
    - Crops (rice, corn, wheat)
    - Aquaculture (fish, shrimp)
    - Livestock (cattle, goats)

    Blockchain: Product creation is synced to Hyperledger Fabric for
    product registry transparency and traceability.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create products"
        )

    # Check uniqueness
    existing = db.query(Product).filter(Product.name == product_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already exists"
        )

    product = Product(
        name=product_data.name,
        description=product_data.description,
        is_active=True
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # Queue blockchain write in background (non-blocking)
    background_tasks.add_task(
        _create_product_blockchain,
        product_id=str(product.id),
        product_name=product.name
    )

    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product details by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.get("", response_model=list[ProductResponse])
async def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100
):
    """List all available products"""
    query = db.query(Product)

    if active_only:
        query = query.filter(Product.is_active == True)

    products = query.offset(skip).limit(limit).all()
    return products


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update product (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update products"
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if product_data.description is not None:
        product.description = product_data.description
    if product_data.is_active is not None:
        product.is_active = product_data.is_active

    db.commit()
    db.refresh(product)

    return product


@router.post("/{product_id}/disable")
async def disable_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable a product type (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can disable products"
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.is_active = False
    db.commit()
    db.refresh(product)

    return {
        "id": product.id,
        "name": product.name,
        "is_active": product.is_active,
        "message": "Product disabled successfully"
    }


@router.post("/{product_id}/enable")
async def enable_product(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable a product type (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can enable products"
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.is_active = True
    db.commit()
    db.refresh(product)

    return {
        "id": product.id,
        "name": product.name,
        "is_active": product.is_active,
        "message": "Product enabled successfully"
    }
