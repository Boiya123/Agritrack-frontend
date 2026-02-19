# 🔗 Backend-Frontend Integration Audit & Roadmap

**Purpose:** Complete wiring audit, missing parts identification, and presentation blueprint.

---

## 📊 BACKEND API INVENTORY (What Exists)

### 1. **Auth Routes** (`/auth`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/auth/register` | POST | User registration | ✅ WIRED (LoginPopup) |
| `/auth/login` | POST | User login | ✅ WIRED (LoginPopup) |
| `/auth/refresh` | POST | Refresh auth token | ❌ MISSING UI |
| `/auth/validate-role/{role}` | GET | Check user role | ❌ MISSING UI |
| `/auth/password-reset` | POST | Request password reset | ❌ MISSING UI |
| `/auth/password-change` | PUT | Change password | ❌ MISSING UI |
| `/auth/logout` | POST | Logout user | ✅ WIRED (StoreContext) |
| `/auth/me` | GET | Get current user | ✅ WIRED (StoreContext) |

### 2. **Products Routes** (`/products`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/products` | POST | Create product type | ✅ WIRED (AddProduct page) |
| `/products` | GET | List products | ✅ WIRED (Operations, Dashboard) |
| `/products/{id}` | GET | Get product details | ❌ MISSING UI |
| `/products/{id}` | PUT | Update product | ❌ MISSING UI |
| `/products/{id}/enable` | POST | Enable product | ❌ MISSING UI |
| `/products/{id}/disable` | POST | Disable product | ❌ MISSING UI |

### 3. **Batches Routes** (`/batches`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/batches` | POST | Create batch | ✅ WIRED (Operations) |
| `/batches` | GET | List batches | ✅ WIRED (Operations) |
| `/batches/{id}` | GET | Get batch details | ✅ WIRED (Operations) |
| `/batches/{id}` | PUT | Update batch | ✅ WIRED (Operations) |
| `/batches/{id}/qr-link` | POST | Link QR code | ✅ WIRED (Operations) |
| `/batches/{id}/archive` | POST | Archive batch | ✅ WIRED (Operations) |

### 4. **Lifecycle Routes** (`/lifecycle`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/lifecycle` | POST | Record generic event | ✅ WIRED (Operations) |
| `/lifecycle/batches/{id}/events` | GET | List batch events | ✅ WIRED (Operations) |
| `/lifecycle/{id}` | GET | Get event details | ❌ MISSING UI |
| `/lifecycle/record-vaccination` | POST | Log vaccination | ✅ WIRED (Operations) |
| `/lifecycle/record-medication` | POST | Log medication | ✅ WIRED (Operations) |
| `/lifecycle/record-mortality` | POST | Log mortality | ✅ WIRED (Operations) |
| `/lifecycle/record-weight` | POST | Log weight | ✅ WIRED (Operations) |

### 5. **Logistics Routes** (`/logistics`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/logistics/transports` | POST | Create transport | ✅ WIRED (Operations) |
| `/logistics/transports/{id}` | GET | Get transport | ✅ WIRED (Operations) |
| `/logistics/transports/{id}` | PUT | Update transport | ✅ WIRED (Operations) |
| `/logistics/batches/{id}/transports` | GET | List batch transports | ✅ WIRED (Operations) |
| `/logistics/transports/{id}/mark-completed` | POST | Complete transport | ✅ WIRED (Operations) |
| `/logistics/temperature-logs` | POST | Record temperature | ✅ WIRED (Operations) |
| `/logistics/transports/{id}/temperature-logs` | GET | List temp logs | ✅ WIRED (Operations) |
| `/logistics/transports/{id}/temperature-violations` | GET | Get temp violations | ✅ WIRED (Operations) |

### 6. **Processing Routes** (`/processing`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/processing/records` | POST | Create processing record | ✅ WIRED (Operations) |
| `/processing/records/{id}` | GET | Get processing record | ❌ MISSING UI |
| `/processing/batches/{id}/records` | GET | List batch records | ✅ WIRED (Operations) |
| `/processing/records/{id}` | PUT | Update record | ✅ WIRED (Operations) |
| `/processing/certifications` | POST | Create certification | ✅ WIRED (Operations) |
| `/processing/certifications/{id}` | GET | Get certification | ❌ MISSING UI |
| `/processing/records/{id}/certifications` | GET | List certifications | ✅ WIRED (Operations) |
| `/processing/certifications/{id}` | PUT | Update certification | ✅ WIRED (Operations) |
| `/processing/certifications/{id}/approve` | POST | Approve cert | ✅ WIRED (Operations) |
| `/processing/certifications/{id}/reject` | POST | Reject cert | ✅ WIRED (Operations) |

### 7. **Regulatory Routes** (`/regulatory`)
| Endpoint | Method | Purpose | Frontend Status |
|----------|--------|---------|-----------------|
| `/regulatory/records` | POST | Create regulatory record | ✅ WIRED (Operations) |
| `/regulatory/records/{id}` | GET | Get regulatory record | ❌ MISSING UI |
| `/regulatory/batches/{id}/records` | GET | List batch records | ✅ WIRED (Operations) |
| `/regulatory/records/{id}` | PUT | Update record | ✅ WIRED (Operations) |
| `/regulatory/records/{id}/approve` | POST | Approve record | ✅ WIRED (Operations) |
| `/regulatory/records/{id}/reject` | POST | Reject record | ✅ WIRED (Operations) |
| `/regulatory/records/{id}/add-audit-flag` | POST | Add audit flag | ✅ WIRED (Operations) |
| `/regulatory/farmers/{id}/compliance-status` | GET | Get compliance status | ✅ WIRED (Dashboard, Operations) |

---

## ❌ MISSING FRONTEND COMPONENTS

### **HIGH PRIORITY** (Easy to add, high value)

#### 1. **Account Settings Page** 
**What's missing:** A page for users to:
- View their profile (name, email, role)
- Change password (API ready: `/auth/password-change`)
- Request password reset (API ready: `/auth/password-reset`)
- Refresh/validate auth token

**Backend Support:** `authApi.passwordChange()`, `authApi.passwordReset()`, `authApi.validateRole()`, `authApi.refresh()`

**File to create:** `frontend/src/pages/AccountSettings/AccountSettings.jsx`

---

#### 2. **Product Management Page** (Admin-only)
**What's missing:** A page for admins to:
- View all products (same as list, but admin-focused)
- Edit product details (update description, metadata)
- Enable/disable products
- Delete or archive products

**Backend Support:** `productsApi.update()`, `productsApi.enable()`, `productsApi.disable()`

**File to create:** `frontend/src/pages/ProductManagement/ProductManagement.jsx`

---

#### 3. **Batch Detail & History Page**
**What's missing:** A detail view for a single batch showing:
- Batch info (ID, farmer, product, quantity, dates)
- Full lifecycle audit trail (all events in reverse chrono order)
- QR code display/link
- Status progression (CREATED → ACTIVE → COMPLETED)
- Related transports and processing records

**Backend Support:** `batchesApi.get()`, `lifecycleApi.listByBatch()`, `logisticsApi.listTransportsByBatch()`, `processingApi.listRecordsByBatch()`

**File to create:** `frontend/src/pages/BatchDetail/BatchDetail.jsx`

---

#### 4. **Transport & Cold Chain Tracking Page**
**What's missing:** A dedicated page to:
- View all transports for a batch
- See temperature logs and violations
- View chain-of-custody timeline
- Mark transport as completed

**Backend Support:** Already wired in Operations, but deserves its own page for clarity

**File to create:** `frontend/src/pages/TransportTracking/TransportTracking.jsx`

---

#### 5. **Compliance & Regulatory Dashboard** (Regulator-only)
**What's missing:** A regulator view to:
- View all pending/approved/rejected regulatory records
- Approve or reject records with reason
- Add audit flags
- View farmer compliance summary

**Backend Support:** All regulatory endpoints already in API

**File to create:** `frontend/src/pages/RegulatoryDashboard/RegulatoryDashboard.jsx`

---

### **MEDIUM PRIORITY** (Enhances UX, moderate effort)

#### 6. **Role-Based Route Gating**
**What's missing:** Frontend doesn't check user role before rendering pages.

**Problem:**  
- Farmers see the admin "AddProduct" button  
- Regulators see operations they can't perform  
- Users hit 403 errors instead of seeing appropriate UI

**Solution:** Add role checks in each page component.

**Example fix:**
```jsx
const allowedRoles = new Set(['ADMIN', 'FARMER']);
if (!allowedRoles.has(currentUser?.role)) {
  return <AccessDenied />;
}
```

**Files to update:**
- `frontend/src/pages/AddProduct/AddProduct.jsx` (ADMIN only)
- `frontend/src/pages/Operations/Operations.jsx` (Role-specific forms)
- `frontend/src/pages/Dashboard/Dashboard.jsx` (ADMIN/REGULATOR only)

---

#### 7. **Blockchain Status Indicator**
**What's missing:** Visual feedback for blockchain sync status.

**Currently:** Generic "queued for blockchain sync" message.

**Missing:** Show actual sync status (pending → confirmed → failed) with timestamps.

**Example:**
```jsx
{batch.blockchain_status === 'pending' && <Spinner />}
{batch.blockchain_status === 'confirmed' && <Checkmark />}
{batch.blockchain_status === 'failed' && <Error reason={batch.blockchain_error} />}
```

**Files to update:**
- `frontend/src/pages/Operations/Operations.jsx` (all forms)
- `frontend/src/pages/BatchDetail/BatchDetail.jsx` (proposed)

---

#### 8. **Real Checkout Flow** 
**What's missing:** Cart and PlaceOrder pages are UI-only; no actual order submission.

**Files:** `frontend/src/pages/Cart/Cart.jsx`, `frontend/src/pages/PlaceOrder/PlaceOrder.jsx`

**Note:** No backend API exists for orders yet. This is out of scope for traceability, but should be flagged if you're selling products.

---

### **LOW PRIORITY** (Nice-to-have)

#### 9. **Event Detail Modal**
**What's missing:** Click a lifecycle event to see full details (metadata, recorded_by, timestamp).

**Backend support:** `lifecycleApi.get()` endpoint exists but isn't used in Frontend.

---

#### 10. **Search & Filter UI**
**What's missing:** Frontend doesn't expose backend query params (`skip`, `limit`, `active_only`).

**Improvement:** Add pagination and filtering dropdowns to list views.

---

## 🔧 WIRING SUMMARY TABLE

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| **Auth** | ✅ 8 endpoints | ⚠️ 2/8 wired | 25% |
| **Products** | ✅ 6 endpoints | ⚠️ 2/6 wired | 33% |
| **Batches** | ✅ 6 endpoints | ✅ 6/6 wired | **100%** |
| **Lifecycle** | ✅ 7 endpoints | ✅ 7/7 wired | **100%** |
| **Logistics** | ✅ 8 endpoints | ✅ 8/8 wired | **100%** |
| **Processing** | ✅ 10 endpoints | ✅ 8/10 wired | 80% |
| **Regulatory** | ✅ 8 endpoints | ✅ 7/8 wired | 87% |
| **TOTAL** | **53 endpoints** | **41/53 wired** | **77%** |

---

## 📋 ACTIONABLE ROADMAP (By Priority)

### **Sprint 1: Quick Wins (2–3 hours)**
1. ✅ Add **Account Settings** page (password change, reset)
2. ✅ Add **Product Management** page (enable/disable)
3. ✅ Add **role-based route gating** to existing pages

### **Sprint 2: Deep Features (3–4 hours)**
4. ✅ Add **Batch Detail** page with full audit trail
5. ✅ Add **Transport Tracking** page (dedicated)
6. ✅ Add **Regulatory Dashboard** (regulator-only)

### **Sprint 3: Polish (1–2 hours)**
7. ✅ Add **blockchain status indicators** (pending/confirmed/failed)
8. ✅ Add **pagination & filtering** to list views
9. ✅ Add **event detail modals**

---

## 🎯 FOR YOUR PRESENTATION

**Title:** "Backend-Frontend Integration: 77% Complete + Roadmap"

**Key Points:**
1. **What's done:** 41 of 53 backend endpoints wired and working
2. **What's missing:** 12 endpoints + 6 missing pages + role-based gating
3. **Why it matters:** Frontend currently has gaps that users will hit (403 errors, no password reset, etc.)
4. **Solution:** Simple roadmap to close the gaps (quick wins in Sprint 1)

**Visuals:**
- Pie chart: 77% wired vs 23% remaining
- Bar chart by module (Auth 25%, Products 33%, Batches 100%, etc.)
- Screenshots of current UI vs proposed UI

**One-liner:**
"I've wired 77% of the backend to the frontend. The remaining 12 endpoints are easy additions—3 new pages and some role-checking tweaks will complete the system."

---

## 📂 Files to Create/Update

**Create:**
- `frontend/src/pages/AccountSettings/AccountSettings.jsx`
- `frontend/src/pages/ProductManagement/ProductManagement.jsx`
- `frontend/src/pages/BatchDetail/BatchDetail.jsx`
- `frontend/src/pages/TransportTracking/TransportTracking.jsx`
- `frontend/src/pages/RegulatoryDashboard/RegulatoryDashboard.jsx`
- `frontend/src/components/RoleGate/RoleGate.jsx` (helper)
- `frontend/src/components/BlockchainStatus/BlockchainStatus.jsx` (helper)

**Update:**
- `frontend/src/App.jsx` (add new routes)
- `frontend/src/pages/Operations/Operations.jsx` (role checks)
- `frontend/src/pages/Dashboard/Dashboard.jsx` (role checks)
- `frontend/src/pages/AddProduct/AddProduct.jsx` (role checks)

---

**Generated:** 2026-02-13  
**Status:** Ready for Sprint Planning
