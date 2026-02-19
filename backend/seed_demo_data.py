"""
Script to seed demo data into the database for presentation purposes.
Run this once to populate test data.
"""
import sys
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.user_model import User, UserRole
from app.models.domain_models import Product, Batch, LifecycleEvent, BatchStatus, LifecycleEventType, RegulatoryRecord, ProcessingRecord, Certification
from app.core.security import hash_password
from uuid import uuid4
from datetime import datetime, timedelta, timezone

def seed_demo_data():
    """Populate database with demo data for presentation"""
    db: Session = SessionLocal()
    
    try:
        # Clear existing demo data (optional)
        # db.query(Batch).delete()
        # db.query(Product).delete()
        # db.query(User).delete()
        # db.commit()
        
        print("🌱 Seeding demo data...")
        
        # Create demo users if they don't exist
        users_data = [
            {
                "email": "farmer1@demo.com",
                "name": "Juan dela Cruz",
                "password": "demo123456",
                "role": UserRole.FARMER
            },
            {
                "email": "farmer2@demo.com",
                "name": "Maria Santos",
                "password": "demo123456",
                "role": UserRole.FARMER
            },
            {
                "email": "admin@demo.com",
                "name": "Admin User",
                "password": "demo123456",
                "role": UserRole.ADMIN
            },
            {
                "email": "regulator@demo.com",
                "name": "Regulator Officer",
                "password": "demo123456",
                "role": UserRole.REGULATOR
            },
            {
                "email": "supplier@demo.com",
                "name": "Logistics Supplier",
                "password": "demo123456",
                "role": UserRole.SUPPLIER
            }
        ]
        
        users = {}
        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    id=uuid4(),
                    name=user_data["name"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    role=user_data["role"]
                )
                db.add(user)
                db.flush()
                users[user_data["role"].value] = user
                print(f"✅ Created user: {user_data['email']}")
            else:
                users[user_data["role"].value] = existing
                print(f"⏭️  User exists: {user_data['email']}")
        
        db.commit()
        
        # Create products if they don't exist
        products_data = [
            {"name": "Poultry", "description": "Chicken, duck, turkey and other birds"},
            {"name": "Crops", "description": "Rice, corn, wheat and vegetables"},
            {"name": "Aquaculture", "description": "Fish and shrimp"},
            {"name": "Livestock", "description": "Cattle, goats, and other livestock"}
        ]
        
        products = {}
        for prod_data in products_data:
            existing = db.query(Product).filter(Product.name == prod_data["name"]).first()
            if not existing:
                product = Product(
                    id=uuid4(),
                    name=prod_data["name"],
                    description=prod_data["description"],
                    is_active=True
                )
                db.add(product)
                db.flush()
                products[prod_data["name"]] = product
                print(f"✅ Created product: {prod_data['name']}")
            else:
                products[prod_data["name"]] = existing
                print(f"⏭️  Product exists: {prod_data['name']}")
        
        db.commit()
        
        # Create demo batches
        now = datetime.now(timezone.utc)
        batches_data = [
            {
                "farmer_id": users["farmer"].id,
                "product_id": products["Poultry"].id,
                "batch_number": "BATCH-POULTRY-001",
                "quantity": 500,
                "status": BatchStatus.CREATED,
                "location": "Farm House 1"
            },
            {
                "farmer_id": users["farmer"].id,
                "product_id": products["Poultry"].id,
                "batch_number": "BATCH-POULTRY-002",
                "quantity": 300,
                "status": BatchStatus.ACTIVE,
                "location": "Farm House 2"
            },
            {
                "farmer_id": users["farmer"].id,
                "product_id": products["Crops"].id,
                "batch_number": "BATCH-CROPS-001",
                "quantity": 1000,
                "status": BatchStatus.COMPLETED,
                "location": "Rice Field A"
            }
        ]
        
        for batch_data in batches_data:
            existing = db.query(Batch).filter(Batch.batch_number == batch_data["batch_number"]).first()
            if not existing:
                batch = Batch(
                    id=uuid4(),
                    farmer_id=batch_data["farmer_id"],
                    product_id=batch_data["product_id"],
                    batch_number=batch_data["batch_number"],
                    quantity=batch_data["quantity"],
                    status=batch_data["status"],
                    location=batch_data.get("location"),
                    start_date=now
                )
                db.add(batch)
                db.flush()
                
                # Add lifecycle event
                event = LifecycleEvent(
                    id=uuid4(),
                    batch_id=batch.id,
                    event_type=LifecycleEventType.HATCH,
                    description=f"Batch created: {batch_data['batch_number']}",
                    event_date=now,
                    recorded_by=batch_data["farmer_id"]
                )
                db.add(event)
                
                print(f"✅ Created batch: {batch_data['batch_number']} (Status: {batch_data['status'].value})")
            else:
                print(f"⏭️  Batch exists: {batch_data['batch_number']}")
        
        db.commit()
        
        # Create processing records and regulatory approvals for regulators
        print("\n📋 Creating regulatory records for approval workflow...")
        
        # Get the regulator user
        regulator_user = db.query(User).filter(User.role == UserRole.REGULATOR).first()
        
        # Create processing records for first two batches
        batches = db.query(Batch).all()
        
        for idx, batch in enumerate(batches[:2]):  # First two batches
            # Create processing record
            processing = ProcessingRecord(
                id=uuid4(),
                batch_id=batch.id,
                processing_date=now,
                facility_name=f"Processing Facility {chr(65 + idx)}",
                slaughter_count=100 if idx == 0 else 50,
                yield_kg=450 if idx == 0 else 200,
                quality_score=85 + (idx * 5)
            )
            db.add(processing)
            db.flush()
            
            # Create regulatory records with different statuses
            # Pending approval
            pending_record = RegulatoryRecord(
                id=uuid4(),
                batch_id=batch.id,
                record_type="health_cert" if idx == 0 else "export_permit",
                status="pending",
                regulator_id=regulator_user.id,
                details=f"Batch inspection required for {batch.batch_number}. Health and safety standards compliance check."
            )
            db.add(pending_record)
            
            # Already approved
            approved_record = RegulatoryRecord(
                id=uuid4(),
                batch_id=batch.id,
                record_type="compliance_check",
                status="approved",
                regulator_id=regulator_user.id,
                issued_date=now - timedelta(days=2),
                details="Compliance check passed. All standards met."
            )
            db.add(approved_record)
            
            print(f"✅ Created regulatory records for batch: {batch.batch_number}")
        
        # Create a rejected record for the third batch (for historical context)
        if len(batches) > 2:
            rejected_record = RegulatoryRecord(
                id=uuid4(),
                batch_id=batches[2].id,
                record_type="health_cert",
                status="rejected",
                regulator_id=regulator_user.id,
                issued_date=now - timedelta(days=5),
                rejection_reason="Temperature monitoring logs incomplete. Requires resubmission with full temperature data."
            )
            db.add(rejected_record)
            print(f"✅ Created rejected regulatory record for batch: {batches[2].batch_number}")
        
        db.commit()
        
        print("✅ Regulatory approval records created successfully!")
        print("\n🔍 Regulator Dashboard will show:")
        print("   - Pending approvals for action")
        print("   - Approved records for reference")
        print("   - Rejected records with reasons")
        
        db.commit()
        print("\n📋 Demo Credentials:")
        print("  Farmer: farmer1@demo.com / demo123456")
        print("  Admin:  admin@demo.com / demo123456")
        print("  Regulator: regulator@demo.com / demo123456")
        print("  Supplier: supplier@demo.com / demo123456")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
