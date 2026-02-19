# 🏗️ AGRITRACK - SYSTEM ARCHITECTURE & WORKFLOWS

## 📐 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT BROWSER                          │
│  (React App at http://localhost:5173)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │  StoreContext (Global Auth State)                │      │
│  │  - currentUser                                   │      │
│  │  - token (JWT)                                   │      │
│  │  - login/logout methods                          │      │
│  └──────────────────────────────────────────────────┘      │
│           ↑                              ↓                   │
│           │                              │                   │
│  ┌────────┴──────────────────────────────┴─────────┐      │
│  │         React Components / Pages                │      │
│  │  - LoginPopup (auth UI)                         │      │
│  │  - RegulatoryDashboard (approval workflow)      │      │
│  │  - Farmer/Admin/Supplier Dashboards             │      │
│  │  - Batch details, history, forms                │      │
│  └───────────────────┬──────────────────────────────┘      │
└────────────────────┼───────────────────────────────────────┘
                     │ HTTPS + JWT
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            FASTAPI BACKEND                                  │
│    (http://127.0.0.1:8000)                                  │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │  API Routes Layer                              │        │
│  │  ├─ /auth - Authentication endpoints           │        │
│  │  ├─ /batches - Batch management                │        │
│  │  ├─ /regulatory - Approvals/Rejections         │        │
│  │  ├─ /lifecycle - Event logging                 │        │
│  │  ├─ /logistics - Transport tracking            │        │
│  │  ├─ /products - Product management             │        │
│  │  └─ /processing - Processing records           │        │
│  └────────────────────────────────────────────────┘        │
│           ↓ SQLAlchemy ORM                                  │
│  ┌────────────────────────────────────────────────┐        │
│  │  Business Logic Layer                          │        │
│  │  ├─ Authentication (JWT, bcrypt)               │        │
│  │  ├─ Authorization (role checking)              │        │
│  │  ├─ Batch workflows                            │        │
│  │  └─ Regulatory workflows                       │        │
│  └────────────────────────────────────────────────┘        │
│           ↓ SQL Queries                                     │
│  ┌────────────────────────────────────────────────┐        │
│  │  Database Session & Connection Pool            │        │
│  └────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                     │ TCP/IP
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                        │
│  (localhost:5432)                                           │
│                                                              │
│  ┌─────────────┬───────────────┬─────────────┬──────────┐ │
│  │  users      │  products     │  batches    │ lifecycle│ │
│  │  ├─ id      │  ├─ id        │  ├─ id      │ events   │ │
│  │  ├─ email   │  ├─ name      │  ├─ batch_# │ ├─ id    │ │
│  │  ├─ pwd     │  ├─ desc      │  ├─ status  │ ├─ type  │ │
│  │  └─ role    │  └─ active    │  └─ qty     │ └─ date  │ │
│  └─────────────┴───────────────┴─────────────┴──────────┘ │
│                                                              │
│  ┌──────────────────┬───────────────┬──────────────────┐  │
│  │ regulatory_      │ transports    │ processing_      │  │
│  │ records          │ ├─ id         │ records          │  │
│  │ ├─ status        │ ├─ batch_id   │ ├─ batch_id      │  │
│  │ ├─ approved/     │ ├─ from/to    │ ├─ facility      │  │
│  │ │ rejected       │ └─ departure  │ └─ yield         │  │
│  │ └─ reason        │               │                  │  │
│  └──────────────────┴───────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 USER AUTHENTICATION FLOW

```
USER ATTEMPTS LOGIN
    │
    ├─ Email: farmer1@demo.com
    ├─ Password: demo123456
    └─ Role: FARMER
         │
         ↓
    [React LoginPopup Component]
         │
         ├─ Validate inputs
         └─ POST /auth/login
              │
              ↓
    [FastAPI Backend]
         │
         ├─ Query: User.email = farmer1@demo.com
         ├─ Compare: hash(password) == stored_hash
         ├─ Verify: user.role == FARMER
         │
         ├─ IF VALID:
         │   ├─ Generate JWT token
         │   │   ├─ Payload: {user_id, email, role, exp: +7days}
         │   │   └─ Signed with secret key
         │   │
         │   └─ Return:
         │       {
         │         "id": "uuid",
         │         "email": "farmer1@demo.com",
         │         "name": "Juan dela Cruz",
         │         "role": "farmer",
         │         "access_token": "eyJhbGc...",
         │         "token_type": "bearer"
         │       }
         │
         ├─ IF INVALID:
         │   └─ Return 401 Unauthorized
         │
         ↓
    [React receives token]
         │
         ├─ Save to localStorage: {agritrack_token, agritrack_user}
         ├─ Update StoreContext.currentUser
         └─ Redirect to dashboard
              │
              ↓
    [Protected Route Check]
         │
         ├─ Token present? ✓
         ├─ Role matches page? ✓
         └─ Navigate to /farmer-dashboard
              │
              ↓
    LOGGED IN & AUTHENTICATED ✅
    
    (All future API calls include JWT in Authorization header)
```

---

## 📋 REGULATORY APPROVAL WORKFLOW

```
FARMER CREATES BATCH
    │
    ├─ Enters: Batch number, quantity, product type, farm location
    ├─ POST /batches
    │
    ↓
BATCH CREATED IN DATABASE
    │
    ├─ Status: "CREATED"
    ├─ blockchain_status: "pending"
    └─ Stored with farmer_id & product_id
         │
         ├─ Auto-insert LifecycleEvent (type: HATCH)
         │
         ↓
    [DASHBOARD: Farmer sees batch in "My Batches"]
         │
         ├─ Farmer can:
         │   ├─ Log new lifecycle events (feeding, medication, etc.)
         │   ├─ Update batch status
         │   └─ Submit for regulatory review
         │
         ↓
    FARMER SUBMITS FOR APPROVAL
         │
         ├─ POST /batches/{id}/submit_for_approval
         ├─ Status changes: "CREATED" → "AWAITING_APPROVAL"
         │
         ↓
    [SYSTEM: Create regulatory_records]
         │
         ├─ status: "PENDING"
         ├─ record_type: "health_cert" | "export_permit"
         ├─ regulator_id: assigned to available regulator
         │
         ↓
    [REGULATOR DASHBOARD: New pending approval appears]
         │
         ├─ Regulator sees:
         │   ├─ Batch number
         │   ├─ Product type & quantity
         │   ├─ Farm location
         │   ├─ Farmer name
         │   └─ Farm history (LifecycleEvents)
         │
         ├─ [APPROVE PATH]:
         │   ├─ Click "Approve"
         │   ├─ PUT /regulatory/records/{id}/approve
         │   ├─ regulatory_records.status = "APPROVED"
         │   ├─ issued_date = NOW
         │   ├─ Auto-create Certificate record
         │   ├─ Farmer notified ✅
         │   └─ Batch now APPROVED for distribution
         │
         └─ [REJECT PATH]:
             ├─ Click "Decline"
             ├─ Enter rejection reason (e.g., "Missing vaccination records")
             ├─ POST /regulatory/records/{id}/reject
             ├─ regulatory_records.status = "REJECTED"
             ├─ rejection_reason = stored with audit trail
             ├─ Farmer notified ❌
             └─ Farmer can correct & resubmit
                  │
                  ├─ Update batch with missing data
                  ├─ Log missing events (vaccinations, etc.)
                  └─ Resubmit (creates new regulatory_record)
                       │
                       ↓
                  [Back to: REGULATOR SEES NEW PENDING]

END STATE:
    ├─ ✅ APPROVED → Batch can proceed in supply chain
    ├─ ❌ REJECTED → Batch awaits correction
    └─ 🔄 RESUBMITTED → New record for regulator review
```

---

## 📊 DATABASE ENTITY RELATIONSHIPS

```
          users (5 total)
            ├─ farmer1, farmer2
            ├─ admin
            ├─ regulator
            └─ supplier
             │
             ├──────────────────┬────────────────────┬──────────┐
             │                  │                    │          │
             ↓                  ↓                    ↓          ↓
         [owns]           [reviews]            [records]   [transports]
             │                │                   │            │
             ↓                ↓                   ↓            ↓
          batches ──→ regulatory_records    lifecycle_     transports
            (3)         (4 pending/         events (3+)      (1+)
                        approved/
                        rejected)
             │
             └──────────────────────────┐
                                        │
                                        ↓
                                    products (4)
                                    ├─ Poultry
                                    ├─ Crops
                                    ├─ Aquaculture
                                    └─ Livestock


BATCH RELATIONSHIPS:
┌────────────────────────────────────────────────────────────┐
│ Batch                                                      │
├────────────────────────────────────────────────────────────┤
│ id (PK)                                                    │
│ product_id (FK) → products                   [many:1]     │
│ farmer_id (FK) → users                       [many:1]     │
│ batch_number (unique)                                     │
│ status: CREATED | ACTIVE | COMPLETED | ARCHIVED          │
│ lifecycle_events { many } ←─────────────────────┐        │
│ regulatory_records { many } ←──────────────────┐         │
│ transports { many } ←──────────────────────────┤         │
│ blockchain_tx_id, blockchain_status           │          │
└────────────────────────────────────────────────┘          │
                                                │            │
                         ┌──────────────────────┼────────┐  │
                         │                      │        │  │
                         ↓                      ↓        ↓  ↓
                    LifecycleEvent       RegulatoryRecord Transport
                    - event_type         - status          - vehicle_id
                    - description        - approved_by     - departure
                    - event_date         - rejection_reason- arrival
                    - recorded_by        - issued_date
```

---

## 🎯 KEY API REQUEST/RESPONSE EXAMPLES

### 1. Login Request/Response
```
REQUEST:
POST /auth/login
Content-Type: application/json
{
  "email": "farmer1@demo.com",
  "password": "demo123456"
}

RESPONSE (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "farmer1@demo.com",
  "name": "Juan dela Cruz",
  "role": "farmer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

Headers set:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Get Regulatory Records
```
REQUEST:
GET /api/regulatory/records
Headers: Authorization: Bearer <token>

RESPONSE (200 OK):
[
  {
    "id": "uuid1",
    "batch_id": "uuid2",
    "batch_number": "BATCH-POULTRY-001",
    "record_type": "health_cert",
    "status": "pending",
    "regulator_id": "uuid3",
    "details": "Batch inspection required...",
    "rejection_reason": null,
    "issued_date": null,
    "created_at": "2026-02-20T06:42:00Z"
  },
  {
    "id": "uuid4",
    "batch_id": "uuid2",
    "batch_number": "BATCH-POULTRY-001",
    "record_type": "compliance_check",
    "status": "approved",
    "regulator_id": "uuid3",
    "details": "Compliance check passed.",
    "rejection_reason": null,
    "issued_date": "2026-02-20T06:42:00Z",
    "created_at": "2026-02-18T00:00:00Z"
  }
]
```

### 3. Approve Batch
```
REQUEST:
POST /api/regulatory/records/uuid1/approve
Headers: Authorization: Bearer <token>
Content-Type: application/json

RESPONSE (200 OK):
{
  "id": "uuid1",
  "status": "approved",
  "issued_date": "2026-02-20T06:45:00Z",
  "message": "Record approved successfully"
}
```

### 4. Reject Batch
```
REQUEST:
POST /api/regulatory/records/uuid1/reject
Headers: Authorization: Bearer <token>
Content-Type: application/json
{
  "rejection_reason": "Temperature monitoring logs incomplete. Requires resubmission with full temperature data."
}

RESPONSE (200 OK):
{
  "id": "uuid1",
  "status": "rejected",
  "rejection_reason": "Temperature monitoring logs incomplete...",
  "message": "Record rejected successfully"
}
```

---

## 🔒 AUTHENTICATION & AUTHORIZATION FLOW

```
USER REQUEST:
GET /batches/my-batches
Headers: Authorization: Bearer eyJhbGc...

      ↓
FASTAPI MIDDLEWARE:

1. Extract token from Authorization header
   - Header format: "Bearer <token>"
   - Extract: <token>

2. Validate JWT signature
   - Decode token using SECRET_KEY
   - Verify: Token not tampered with

3. Check expiration
   - exp_time < current_time?
   - If yes: Token expired (401)
   - If no: Valid (continue)

4. Extract payload
   {
     "user_id": "uuid",
     "email": "farmer1@demo.com",
     "role": "farmer",
     "exp": 1708555200
   }

      ↓
ROUTE HANDLER:

5. Get user from database using user_id
   - Confirm user still exists
   - Confirm user.role == "farmer"

6. Check endpoint authorization
   - Role check: "farmer" can access /batches/my-batches? ✓
   - If role mismatch: 403 Forbidden

      ↓
ROUTE EXECUTION:

7. Execute business logic
   - Query: batches WHERE farmer_id = "uuid"
   - Return: User's batches only

      ↓
RESPONSE (200 OK):
[
  {batch1},
  {batch2},
  {batch3}
]
```

---

## 📱 ROLE-BASED ACCESS CONTROL MATRIX

```
Feature              │ Farmer │ Admin │ Regulator │ Supplier
─────────────────────┼────────┼───────┼───────────┼──────────
Create Batch         │   ✓    │   ✗   │     ✗     │    ✗
View Own Batches     │   ✓    │   ✗   │     ✗     │    ✗
View All Batches     │   ✗    │   ✓   │     ✓     │    ✗
Log Events           │   ✓    │   ✗   │     ✗     │    ✗
View Regulations     │   ✓    │   ✓   │     ✓     │    ✓
Approve/Reject       │   ✗    │   ✗   │     ✓     │    ✗
Manage Products      │   ✗    │   ✓   │     ✗     │    ✗
Create Transport     │   ✓    │   ✗   │     ✗     │    ✓
Track Shipment       │   ✓    │   ✓   │     ✓     │    ✓
```

---

## 🚀 SCALING ARCHITECTURE (Future)

```
Current (MVP):
    1 Backend Instance ← → 1 PostgreSQL DB

Future (Scaled):
    ┌─────────────────────────────────────────────┐
    │         AWS / Cloud Platform                │
    │                                             │
    │  ┌──────────────────────────────────────┐  │
    │  │    Load Balancer (nginx/ALB)         │  │
    │  │    - Route requests to backends      │  │
    │  │    - SSL/TLS termination             │  │
    │  └──────────────────────────────────────┘  │
    │         ↓    ↓    ↓    ↓                   │
    │  ┌──────────────────────────────────────┐  │
    │  │  Backend Instances (Auto-scaling)    │  │
    │  │  - Instance 1 (FastAPI)              │  │
    │  │  - Instance 2 (FastAPI)              │  │
    │  │  - Instance 3 (FastAPI)              │  │
    │  │  - Instance N (FastAPI)              │  │
    │  └──────────────────────────────────────┘  │
    │         ↓    (Connection Pool)             │
    │  ┌──────────────────────────────────────┐  │
    │  │   Database Cluster (PostgreSQL)      │  │
    │  │   - Primary (Write)                  │  │
    │  │   - Read Replicas (Query)            │  │
    │  │   - Automated Failover               │  │
    │  └──────────────────────────────────────┘  │
    │         ↓                                   │
    │  ┌──────────────────────────────────────┐  │
    │  │  Cache Layer (Redis)                 │  │
    │  │  - Session tokens                    │  │
    │  │  - Batch queries                     │  │
    │  └──────────────────────────────────────┘  │
    │         ↓                                   │
    │  ┌──────────────────────────────────────┐  │
    │  │  Message Queue (RabbitMQ/Kafka)      │  │
    │  │  - Blockchain sync service           │  │
    │  │  - Email notifications               │  │
    │  │  - Audit logging                     │  │
    │  └──────────────────────────────────────┘  │
    │         ↓                                   │
    │  ┌──────────────────────────────────────┐  │
    │  │  WebSocket Server (Real-time)        │  │
    │  │  - Live batch updates                │  │
    │  │  - Approval notifications            │  │
    │  │  - Supply chain tracking              │  │
    │  └──────────────────────────────────────┘  │
    │         ↓                                   │
    │  ┌──────────────────────────────────────┐  │
    │  │  Blockchain Service                  │  │
    │  │  - Hyperledger Fabric client         │  │
    │  │  - Auto-sync batches & events        │  │
    │  │  - Generate audit proofs             │  │
    │  └──────────────────────────────────────┘  │
    │                                             │
    │  CDN (CloudFront/Cloudflare)               │
    │  - Frontend static assets                  │
    │  - Global distribution                     │
    │  - Image optimization                      │
    └─────────────────────────────────────────────┘
```

---

**This covers the complete architecture! Good luck with your defense! 🎓**
