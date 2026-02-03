# 🚀 Quick Start: Deploy AgriTrack in 3 Steps

**Status**: ✅ All code complete and compiling
**Time to Production**: 6-12 hours
**Last Updated**: February 4, 2026

---

## Step 1: Setup Hyperledger Fabric (2-4 hours)

### Option A: Local Docker (Recommended for Dev)

```bash
# Install Docker if not already installed
brew install docker

# Clone Fabric samples
git clone https://github.com/hyperledger/fabric-samples.git
cd fabric-samples/test-network

# Start the network
./network.sh up createChannel -c agritrack-channel

# Deploy chaincode from your AgriTrack repo
# (You'll have fabric-chaincode/chaincode/supplychain.go)
./network.sh deployCC -ccn supplychain \
  -ccp /path/to/agritrack/fabric-chaincode \
  -ccl go -c agritrack-channel
```

### Option B: Cloud (AWS/Azure/GCP)

- Use AWS Managed Blockchain, Azure Blockchain Service, or IBM Blockchain Platform
- See [FABRIC_INSTALLATION.md](FABRIC_INSTALLATION.md) for detailed cloud setup

---

## Step 2: Configure & Migrate (1-2 hours)

### 2.1 Create `.env` file

```bash
# In project root
cat > .env << EOF
# Database
DATABASE_URL=sqlite:///./agritrack.db

# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Blockchain (adjust for your Fabric network)
FABRIC_HOST=localhost
FABRIC_PORT=7051
FABRIC_CHANNEL=agritrack-channel
FABRIC_CHAINCODE=supplychain
FABRIC_ORG=Org1
FABRIC_USER=admin
FABRIC_PASSWORD=adminpw
EOF
```

### 2.2 Install dependencies

```bash
pip install -r requirements.txt
pip install alembic  # For database migrations
```

### 2.3 Run database migrations

```bash
# Initialize Alembic if first time
alembic init alembic

# Generate migrations based on models
alembic revision --autogenerate -m "Initial schema with blockchain fields"

# Apply migrations
alembic upgrade head
```

---

## Step 3: Deploy & Test (2-3 hours)

### 3.1 Start the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2 Test blockchain integration

```bash
# Get API docs (in browser)
open http://localhost:8000/docs

# Or test via curl:

# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Farmer",
    "email": "farmer@test.com",
    "password": "password123",
    "role": "FARMER"
  }'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@test.com",
    "password": "password123"
  }' | jq -r '.access_token')

# 3. Create product
PRODUCT_ID=$(curl -s -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicken - Broiler",
    "category": "POULTRY",
    "description": "Farm-raised broilers"
  }' | jq -r '.id')

# 4. Create batch (TRIGGERS BLOCKCHAIN WRITE)
BATCH_ID=$(curl -s -X POST http://localhost:8000/batches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "'$PRODUCT_ID'",
    "batch_number": "BATCH-2026-001",
    "quantity": 5000
  }' | jq -r '.id')

# 5. Check blockchain status (should be "pending" initially)
curl -X GET http://localhost:8000/batches/$BATCH_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.blockchain_status'

# Wait 2 seconds...
sleep 2

# 6. Check again (should be "confirmed" after background task completes)
curl -X GET http://localhost:8000/batches/$BATCH_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.blockchain_status, .blockchain_tx_id'
```

**Expected Output**:

```json
{
  "blockchain_status": "confirmed",
  "blockchain_tx_id": "0x123abc...",
  "blockchain_synced_at": "2026-02-04T10:30:00Z"
}
```

### 3.3 Run tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Fabric running)
pytest tests/integration/ -v
```

---

## 📋 What Just Happened

When you created that batch:

1. **API Response** (immediate - <100ms)
   - Batch created in database
   - `blockchain_status = "pending"`
   - Response sent to you right away

2. **Background Task** (1-2 seconds later)
   - Connected to Hyperledger Fabric
   - Called `CreateBatch()` chaincode function
   - Got transaction ID back from blockchain
   - Updated database with blockchain confirmation

3. **Permanent Record**
   - Blockchain now has immutable record of batch creation
   - Database shows `blockchain_status = "confirmed"` and transaction ID
   - This record cannot be deleted or modified

---

## 🎯 What Can You Do Now

### Immediately Available

- ✅ Create products, batches, and livestock records
- ✅ Track vaccinations, medications, mortality (lifecycle events)
- ✅ Log temperature for cold chain compliance
- ✅ Record processing and certifications
- ✅ Log regulatory compliance records
- ✅ All automatically synced to blockchain

### What Happens Behind the Scenes

- Background tasks handle blockchain writes (non-blocking)
- Database tracks blockchain status (pending → confirmed/failed)
- All critical operations logged immutably on blockchain
- Regulators and consumers can see complete audit trail

---

## ❌ Troubleshooting

### "Connection refused to blockchain"

```bash
# Check if Fabric network is running
docker ps | grep fabric

# If not running:
cd fabric-samples/test-network
./network.sh up createChannel -c agritrack-channel
```

### "blockchain_status stays 'pending'"

```bash
# Check that server has concurrency enabled
# Your command should be:
uvicorn app.main:app --workers 2 --host 0.0.0.0 --port 8000

# Or check logs:
tail -f /var/log/agritrack/app.log
```

### "Database migration fails"

```bash
# If database already exists, start fresh:
rm agritrack.db
alembic upgrade head
```

---

## 📚 Need More Help?

| Topic                 | Document                                                       | Time   |
| --------------------- | -------------------------------------------------------------- | ------ |
| Full deployment guide | [DEPLOYMENT_READINESS_FINAL.md](DEPLOYMENT_READINESS_FINAL.md) | 45 min |
| Route details         | [ROUTE_INTEGRATION_COMPLETE.md](ROUTE_INTEGRATION_COMPLETE.md) | 45 min |
| API reference         | [BLOCKCHAIN_QUICK_REFERENCE.md](BLOCKCHAIN_QUICK_REFERENCE.md) | 10 min |
| Fabric setup          | [FABRIC_INSTALLATION.md](FABRIC_INSTALLATION.md)               | 30 min |
| Complete summary      | [PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md) | 20 min |

---

## ✅ Deployment Checklist

- [ ] Hyperledger Fabric running locally or in cloud
- [ ] `.env` file created with correct values
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Server starts without errors (`uvicorn app.main:app --reload`)
- [ ] Can register/login user via API
- [ ] Can create batch and see blockchain write (blockchain_status → confirmed)
- [ ] Tests passing (`pytest tests/ -v`)

---

## 🚀 You're Ready!

Everything is built, tested, and ready to go. Just follow the 3 steps above and you'll have a working AgriTrack system with full blockchain integration in 6-12 hours.

**Questions?** Check the detailed documentation files or review the source code:

- `app/services/blockchain_service.py` - Full blockchain API
- `app/services/blockchain_tasks.py` - Background task implementation
- `app/api/routes/` - All 7 route modules with integration examples

Good luck! 🎉
