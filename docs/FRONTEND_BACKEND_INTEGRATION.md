# Frontend + Backend Integration Guide

This guide documents exactly how the frontend talks to the FastAPI backend in this monorepo. It includes request/response shapes, required auth, and UI mapping so you can extend the app safely.

---

## Contents

- [Auth Flow](#auth-flow)
- [API Client](#api-client)
- [Products](#products)
- [Batches](#batches)
- [Lifecycle Events](#lifecycle-events)
- [Logistics](#logistics)
- [Processing](#processing)
- [Regulatory](#regulatory)
- [Frontend Data Mapping](#frontend-data-mapping)
- [Role Matrix](#role-matrix)
- [Error Handling Conventions](#error-handling-conventions)

---

## Auth Flow

### Login

**Request**

```
POST /auth/login
Content-Type: application/json

{
  "email": "farmer@test.com",
  "password": "password123"
}
```

**Response**

```
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "<uuid>",
  "role": "farmer"
}
```

### Register

**Request**

```
POST /auth/register
Content-Type: application/json

{
  "name": "Test Farmer",
  "email": "farmer@test.com",
  "password": "password123",
  "role": "FARMER"
}
```

**Response**

```
{
  "id": "<uuid>",
  "email": "farmer@test.com",
  "name": "Test Farmer",
  "role": "farmer"
}
```

### Token Storage

Frontend stores:

- `localStorage.agritrack_token`
- `localStorage.agritrack_user`

These are applied to API requests as:

```
Authorization: Bearer <token>
```

### Additional Auth Endpoints

- `POST /auth/logout` (invalidates token)
- `GET /auth/me` (current user profile)
- `POST /auth/password-reset?email=<email>`
- `PUT /auth/password-change?old_password=<old>&new_password=<new>`

---

## API Client

Main client file:

- `frontend/src/api/client.js`

Key features:

- Uses `VITE_API_BASE_URL` to build URLs
- Adds `Authorization` header when token is provided
- Returns JSON data or throws for non-2xx responses

---

## Products

### List Products

**Request**

```
GET /products?active_only=true
Authorization: Bearer <token>
```

**Response**

```
[
  {
    "id": "<uuid>",
    "name": "Poultry - Broiler",
    "description": "Farm-raised broilers",
    "is_active": true,
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": null
  }
]
```

### Create Product Type

**Request**

```
POST /products
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Poultry - Broiler",
  "description": "Farm-raised broilers"
}
```

### Additional Product Endpoints

- `PUT /products/{product_id}`
- `POST /products/{product_id}/enable`
- `POST /products/{product_id}/disable`

---

## Batches

### Create Batch

```
POST /batches
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": "<uuid>",
  "batch_number": "BATCH-2026-001",
  "quantity": 5000,
  "start_date": "2026-02-12T08:00:00Z",
  "expected_end_date": "2026-03-01T08:00:00Z",
  "location": "Farm A",
  "notes": "Initial broiler batch"
}
```

### List Batches

```
GET /batches
Authorization: Bearer <token>
```

### Additional Batch Endpoints

- `PUT /batches/{batch_id}`
- `POST /batches/{batch_id}/qr-link?qr_code=<code>`
- `POST /batches/{batch_id}/archive`

---

## Lifecycle Events

### Record Event

```
POST /lifecycle
Authorization: Bearer <token>
Content-Type: application/json

{
  "batch_id": "<uuid>",
  "event_type": "VACCINATION",
  "description": "Vaccinated with A7",
  "event_date": "2026-02-12T09:00:00Z",
  "quantity_affected": 4800,
  "event_metadata": "{\"vaccine\": \"A7\"}"
}
```

### List Events by Batch

```
GET /lifecycle/batches/<batch_id>/events
Authorization: Bearer <token>
```

### Quick Lifecycle Endpoints

- `POST /lifecycle/record-vaccination`
- `POST /lifecycle/record-medication`
- `POST /lifecycle/record-mortality`
- `POST /lifecycle/record-weight`

---

## Logistics

### Create Transport

```
POST /logistics/transports
Authorization: Bearer <token>
Content-Type: application/json

{
  "batch_id": "<uuid>",
  "to_party_id": "<uuid>",
  "vehicle_id": "TRUCK-44",
  "driver_name": "K. Driver",
  "departure_time": "2026-02-12T12:00:00Z",
  "origin_location": "Farm A",
  "destination_location": "Facility B",
  "temperature_monitored": true,
  "notes": "Keep below 4C"
}
```

### Record Temperature

```
POST /logistics/temperature-logs
Authorization: Bearer <token>
Content-Type: application/json

{
  "transport_id": "<uuid>",
  "temperature": 3.8,
  "timestamp": "2026-02-12T12:15:00Z",
  "location": "Checkpoint 1"
}
```

### List Transports by Batch

```
GET /logistics/batches/<batch_id>/transports
Authorization: Bearer <token>
```

### Additional Logistics Endpoints

- `PUT /logistics/transports/{transport_id}`
- `POST /logistics/transports/{transport_id}/mark-completed`
- `GET /logistics/transports/{transport_id}/temperature-logs`
- `GET /logistics/transports/{transport_id}/temperature-violations`

---

## Processing

### Create Processing Record

```
POST /processing/records
Authorization: Bearer <token>
Content-Type: application/json

{
  "batch_id": "<uuid>",
  "processing_date": "2026-02-13T07:00:00Z",
  "facility_name": "Facility B",
  "slaughter_count": 4700,
  "yield_kg": 5300,
  "quality_score": 91,
  "notes": "Passed QA"
}
```

### Issue Certification

```
POST /processing/certifications
Authorization: Bearer <token>
Content-Type: application/json

{
  "processing_record_id": "<uuid>",
  "cert_type": "halal",
  "notes": "Certified by board"
}
```

### List Processing Records

```
GET /processing/batches/<batch_id>/records
Authorization: Bearer <token>
```

### Additional Processing Endpoints

- `PUT /processing/records/{record_id}`
- `GET /processing/records/{record_id}/certifications`
- `PUT /processing/certifications/{cert_id}`
- `POST /processing/certifications/{cert_id}/approve`
- `POST /processing/certifications/{cert_id}/reject?reason=<text>`

---

## Regulatory

### Create Regulatory Record

```
POST /regulatory/records
Authorization: Bearer <token>
Content-Type: application/json

{
  "batch_id": "<uuid>",
  "record_type": "health_cert",
  "details": "Issued by agency"
}
```

### Approve Record

```
POST /regulatory/records/<record_id>/approve
Authorization: Bearer <token>
```

### Reject Record

```
POST /regulatory/records/<record_id>/reject?reason=Insufficient%20documentation
Authorization: Bearer <token>
```

### Additional Regulatory Endpoints

- `PUT /regulatory/records/{record_id}`
- `POST /regulatory/records/{record_id}/add-audit-flag?flag=<flag>`
- `GET /regulatory/farmers/{farmer_id}/compliance-status`

---

## Frontend Data Mapping

Backend products do not include price or image fields. The frontend maps them to UI items with placeholders:

```
{
  _id: product.id,
  name: product.name,
  description: product.description,
  price: null,
  image: assets.header_img,
  category: 'All'
}
```

This allows the marketplace UI to render products even though pricing and imagery are managed outside the backend.

---

## Role Matrix

| Role       | Allowed Domains                                      |
|------------|-------------------------------------------------------|
| FARMER     | Batches, Lifecycle                                    |
| SUPPLIER   | Logistics, Processing, Certifications                 |
| REGULATOR  | Regulatory                                            |
| ADMIN      | All domains, plus product types                       |

---

## Error Handling Conventions

Backend error responses use the `detail` field. The frontend surfaces `detail` if available, otherwise a fallback message.

Common statuses:

- `401` Not authenticated
- `403` Role mismatch / not allowed
- `404` Resource not found
- `400` Validation or uniqueness error

---

If you add new endpoints, update the API layer in `frontend/src/api/index.js` and include the call in the Operations console if it is operationally relevant.
