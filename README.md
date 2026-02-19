# AgriTrack Monorepo (Frontend + Backend)

This repository is a local monorepo that combines the Vite React frontend and the FastAPI backend. The backend history is preserved using git subtree under `backend/`, and the frontend code lives in `frontend/`.

> Note: This repository is local-only unless you choose to push it to a new GitHub repo. The original backend repo remains unchanged.

---

## Table of Contents

- [Repo Layout](#repo-layout)
- [Quick Start (Local)](#quick-start-local)
- [Environment Variables](#environment-variables)
- [Frontend Overview](#frontend-overview)
- [Backend Overview](#backend-overview)
- [Frontend to Backend Integration Map](#frontend-to-backend-integration-map)
- [Operations Console Guide](#operations-console-guide)
- [Auth & Roles](#auth--roles)
- [Common Flows](#common-flows)
- [Troubleshooting](#troubleshooting)

---

## Repo Layout

```
frontend/   # Vite React app (UI)
backend/    # FastAPI backend + blockchain integration
```

---

## Quick Start (Local)

### 1) Frontend

```bash
cd frontend
npm install
npm run dev
```

By default the frontend runs at:

```
http://localhost:5173
```

### 2) Backend

```bash
cd backend
# Create a .env file (see below)
# Install dependencies (requirements.txt is not included yet)
# Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at:

```
http://localhost:8000
```

Open API docs:

```
http://localhost:8000/docs
```

---

## Environment Variables

### Frontend

Create a file at `frontend/.env` or copy from `frontend/.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Backend

Create a `.env` in `backend/` with values required by `backend/app/core/config.py`:

```
# Database
DATABASE_URL=sqlite:///./agritrack.db

# Security
SECRET_KEY=replace-with-a-long-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Hyperledger Fabric (optional for local dev)
FABRIC_CHANNEL=agritrack-channel
FABRIC_CHAINCODE=supplychain
FABRIC_PEER_ENDPOINT=localhost
FABRIC_MSP_ID=Org1MSP
FABRIC_IDENTITY=admin
FABRIC_TLS_CA_CERT=/path/to/tls/ca.crt
FABRIC_IDENTITY_CERT=/path/to/identity/cert.pem
FABRIC_IDENTITY_KEY=/path/to/identity/key.pem
```

---

## Frontend Overview

Main UI routes:

- `/` Home + product display
- `/cart` Cart summary
- `/order` Checkout form
- `/add-product` Admin product type creation
- `/ops` Operations console (batches, lifecycle, logistics, processing, regulatory)

Key frontend files:

- `frontend/src/context/StoreContext.jsx` (auth, token storage, products, cart)
- `frontend/src/api/` (API clients and endpoints)
- `frontend/src/pages/Operations/Operations.jsx` (full backend workflow UI)

---

## Backend Overview

The API is FastAPI with the following route groups:

- `/auth` (register, login, refresh, validate-role)
- `/products` (product types)
- `/batches` (production batches)
- `/lifecycle` (audit events)
- `/logistics` (transport + temperature logs)
- `/processing` (processing records + certifications)
- `/regulatory` (compliance records)

Entry point: `backend/app/main.py`

---

## Frontend to Backend Integration Map

### Auth

Backend:
- POST `/auth/register`
- POST `/auth/login`

Frontend:
- `frontend/src/components/LoginPopup/LoginPopup.jsx`
- `frontend/src/context/StoreContext.jsx`

Token storage:
- `localStorage.agritrack_token`
- `localStorage.agritrack_user`

### Products

Backend:
- GET `/products`
- POST `/products`

Frontend:
- `frontend/src/pages/AddProduct/AddProduct.jsx` (create product type)
- `frontend/src/context/StoreContext.jsx` (load products)

### Batches

Backend:
- POST `/batches`
- GET `/batches`

Frontend:
- `frontend/src/pages/Operations/Operations.jsx` (Create Batch + list)

### Lifecycle Events

Backend:
- POST `/lifecycle`
- GET `/lifecycle/batches/{batch_id}/events`

Frontend:
- `frontend/src/pages/Operations/Operations.jsx` (Record + load events)

### Logistics

Backend:
- POST `/logistics/transports`
- POST `/logistics/temperature-logs`
- GET `/logistics/batches/{batch_id}/transports`

Frontend:
- `frontend/src/pages/Operations/Operations.jsx` (Transport + temperature log)

### Processing

Backend:
- POST `/processing/records`
- POST `/processing/certifications`
- GET `/processing/batches/{batch_id}/records`

Frontend:
- `frontend/src/pages/Operations/Operations.jsx` (Processing + certification)

### Regulatory

Backend:
- POST `/regulatory/records`
- POST `/regulatory/records/{record_id}/approve`
- POST `/regulatory/records/{record_id}/reject`
- GET `/regulatory/batches/{batch_id}/records`

Frontend:
- `frontend/src/pages/Operations/Operations.jsx` (Create + approve/reject)

---

## Operations Console Guide

Open:

```
http://localhost:5173/ops
```

The Operations console is a unified UI for all backend domains. It is designed to test and operate each API group without needing a separate admin app.

What you can do:

1. **Create Batches**
   - Select a product type
   - Provide a batch number, quantity, and start date
   - Optional location and notes

2. **Record Lifecycle Events**
   - Attach events to a batch
   - Use consistent event types (vaccination, medication, feeding, etc.)

3. **Create Transport Manifests**
   - Assign to-party IDs
   - Track origin/destination and timing

4. **Temperature Logs**
   - Log cold-chain readings
   - Backend validates and flags violations

5. **Processing Records**
   - Capture facility details
   - Include yield/quality data

6. **Certifications**
   - Issue halal/organic/quality certifications

7. **Regulatory Actions**
   - Create compliance records
   - Approve or reject with reasons

---

## Auth & Roles

Backend roles:

- `FARMER` - create batches, lifecycle events
- `SUPPLIER` - create processing records, logistics
- `REGULATOR` - regulatory actions
- `ADMIN` - manage products and approve everything

The frontend stores the role in `localStorage` and surfaces it in the Operations console header.

---

## Common Flows

### 1) Product + Batch

1. Login as `ADMIN`
2. Create product type in `/add-product`
3. Login as `FARMER`
4. Create batch in `/ops`

### 2) Traceability

1. Create batch
2. Record lifecycle events (vaccination, mortality)
3. Add transport manifest
4. Record temperature logs
5. Create processing record
6. Issue certification
7. Create regulatory record and approve

---

## Troubleshooting

### CORS Errors in Browser

CORS is enabled in `backend/app/main.py` for the standard Vite dev ports. If your port differs, update the allowed origins list.

### API 401 Unauthorized

All major routes require a valid access token. Login first via the popup, or use the API docs to get a token and set it in local storage.

### Backend Dependencies

The backend docs mention `requirements.txt`, but it is not included. You can generate one by:

```
cd backend
pip freeze > requirements.txt
```

### Environment Variables Not Loading

The backend uses `dotenv`. Confirm your `.env` file lives in `backend/` and that you restart the server after changes.
