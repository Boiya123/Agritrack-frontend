from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================================================
# Product Schemas
# ============================================================================

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Batch Schemas
# ============================================================================

class BatchCreate(BaseModel):
    product_id: UUID
    batch_number: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0)
    start_date: datetime
    expected_end_date: Optional[datetime] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class BatchUpdate(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    actual_end_date: Optional[datetime] = None
    qr_code: Optional[str] = None
    notes: Optional[str] = None


class BatchResponse(BaseModel):
    id: UUID
    product_id: UUID
    farmer_id: UUID
    batch_number: str
    status: str
    quantity: int
    start_date: datetime
    expected_end_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    location: Optional[str]
    qr_code: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Lifecycle Event Schemas
# ============================================================================

class LifecycleEventCreate(BaseModel):
    batch_id: UUID
    event_type: str  # vaccination, medication, weight_measurement, etc.
    description: str = Field(..., min_length=1)
    event_date: datetime
    quantity_affected: Optional[int] = None
    event_metadata: Optional[str] = None  # JSON string for additional details


class LifecycleEventResponse(BaseModel):
    id: UUID
    batch_id: UUID
    event_type: str
    description: str
    recorded_by: UUID
    event_date: datetime
    quantity_affected: Optional[int]
    event_metadata: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Transport/Logistics Schemas
# ============================================================================

class TransportCreate(BaseModel):
    batch_id: UUID
    to_party_id: UUID
    vehicle_id: Optional[str] = None
    driver_name: Optional[str] = None
    departure_time: datetime
    origin_location: str = Field(..., min_length=1)
    destination_location: str = Field(..., min_length=1)
    temperature_monitored: bool = False
    notes: Optional[str] = None


class TransportUpdate(BaseModel):
    arrival_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TransportResponse(BaseModel):
    id: UUID
    batch_id: UUID
    from_party_id: UUID
    to_party_id: UUID
    vehicle_id: Optional[str]
    driver_name: Optional[str]
    departure_time: datetime
    arrival_time: Optional[datetime]
    origin_location: str
    destination_location: str
    temperature_monitored: bool
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TemperatureLogCreate(BaseModel):
    transport_id: UUID
    temperature: float = Field(..., ge=-50, le=50)  # Reasonable temperature range
    timestamp: datetime
    location: Optional[str] = None


class TemperatureLogResponse(BaseModel):
    id: UUID
    transport_id: UUID
    temperature: float
    timestamp: datetime
    location: Optional[str]
    is_violation: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Processing Schemas
# ============================================================================

class ProcessingRecordCreate(BaseModel):
    batch_id: UUID
    processing_date: datetime
    facility_name: str = Field(..., min_length=1)
    slaughter_count: Optional[int] = None
    yield_kg: Optional[float] = None
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class ProcessingRecordUpdate(BaseModel):
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class ProcessingRecordResponse(BaseModel):
    id: UUID
    batch_id: UUID
    processing_date: datetime
    facility_name: str
    slaughter_count: Optional[int]
    yield_kg: Optional[float]
    quality_score: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CertificationCreate(BaseModel):
    processing_record_id: UUID
    cert_type: str = Field(..., min_length=1)  # halal, organic, food_safety, etc.
    notes: Optional[str] = None


class CertificationUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|failed)$")
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class CertificationResponse(BaseModel):
    id: UUID
    processing_record_id: UUID
    cert_type: str
    status: str
    issued_date: Optional[datetime]
    expiry_date: Optional[datetime]
    issuer_id: Optional[UUID]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Regulatory Schemas
# ============================================================================

class RegulatoryRecordCreate(BaseModel):
    batch_id: UUID
    record_type: str = Field(..., min_length=1)  # health_cert, export_permit, etc.
    details: Optional[str] = None


class RegulatoryRecordUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|rejected|conditional)$")
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    audit_flags: Optional[str] = None  # JSON string


class RegulatoryRecordResponse(BaseModel):
    id: UUID
    batch_id: UUID
    record_type: str
    status: str
    issued_date: Optional[datetime]
    expiry_date: Optional[datetime]
    regulator_id: UUID
    details: Optional[str]
    rejection_reason: Optional[str]
    audit_flags: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
