from sqlalchemy import Column, String, Enum, DateTime, Float, Integer, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base
import uuid
from datetime import datetime
import enum


class Product(Base):
    """Product types available in the system (poultry, rice, corn, fish, etc.)"""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g., "poultry", "rice", "corn"
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name})>"


class BatchStatus(enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class Batch(Base):
    """Physical production groups (flocks, harvest lots, crop cycles)"""
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    batch_number = Column(String, unique=True, nullable=False)  # Unique identifier for tracking
    status = Column(Enum(BatchStatus), default=BatchStatus.CREATED, nullable=False)
    quantity = Column(Integer, nullable=False)  # Number of units (animals, kg, etc.)
    start_date = Column(DateTime(timezone=True), nullable=False)
    expected_end_date = Column(DateTime(timezone=True), nullable=True)
    actual_end_date = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)  # Farm location/house
    qr_code = Column(String, unique=True, nullable=True)  # QR system link
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Batch(id={self.id}, batch_number={self.batch_number}, status={self.status})>"


class LifecycleEventType(enum.Enum):
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    WEIGHT_MEASUREMENT = "weight_measurement"
    FEEDING_LOG = "feeding_log"
    MORTALITY = "mortality"
    HATCH = "hatch"
    ENVIRONMENTAL_LOG = "environmental_log"


class LifecycleEvent(Base):
    """Temporal audit trail of batch events"""
    __tablename__ = "lifecycle_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    event_type = Column(Enum(LifecycleEventType), nullable=False)
    description = Column(String, nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    quantity_affected = Column(Integer, nullable=True)  # For mortality, hatch, etc.
    event_metadata = Column(String, nullable=True)  # JSON field for additional details
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<LifecycleEvent(id={self.id}, batch_id={self.batch_id}, event_type={self.event_type})>"


class Transport(Base):
    """Transport manifests and logistics"""
    __tablename__ = "transports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    from_party_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    to_party_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    origin_location = Column(String, nullable=False)
    destination_location = Column(String, nullable=False)
    temperature_monitored = Column(Boolean, default=False)
    status = Column(String, default="in_transit")  # in_transit, arrived, completed
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Transport(id={self.id}, batch_id={self.batch_id})>"


class TemperatureLog(Base):
    """Temperature monitoring during transport"""
    __tablename__ = "temperature_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    transport_id = Column(UUID(as_uuid=True), ForeignKey("transports.id"), nullable=False)
    temperature = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    is_violation = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TemperatureLog(id={self.id}, transport_id={self.transport_id}, temp={self.temperature})>"


class ProcessingRecord(Base):
    """Processing facility records"""
    __tablename__ = "processing_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    processing_date = Column(DateTime(timezone=True), nullable=False)
    facility_name = Column(String, nullable=False)
    slaughter_count = Column(Integer, nullable=True)
    yield_kg = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)  # 0-100
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProcessingRecord(id={self.id}, batch_id={self.batch_id})>"


class Certification(Base):
    """Product certifications (halal, organic, food safety, etc.)"""
    __tablename__ = "certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    processing_record_id = Column(UUID(as_uuid=True), ForeignKey("processing_records.id"), nullable=False)
    cert_type = Column(String, nullable=False)  # halal, organic, food_safety, etc.
    status = Column(String, default="pending")  # pending, approved, failed
    issued_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    issuer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Certification(id={self.id}, cert_type={self.cert_type}, status={self.status})>"


class RegulatoryRecord(Base):
    """Health certificates, permits, regulatory approvals"""
    __tablename__ = "regulatory_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    record_type = Column(String, nullable=False)  # health_cert, export_permit, compliance_check, etc.
    status = Column(String, default="pending")  # pending, approved, rejected, conditional
    issued_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    regulator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    details = Column(String, nullable=True)  # JSON or text with regulatory details
    rejection_reason = Column(String, nullable=True)
    audit_flags = Column(String, nullable=True)  # JSON array of flags
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<RegulatoryRecord(id={self.id}, record_type={self.record_type}, status={self.status})>"
