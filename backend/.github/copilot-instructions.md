# AgriTrack Copilot Instructions

## Project Overview

AgriTrack is a FastAPI-based agricultural traceability and supply chain management system that tracks the lifecycle of agricultural products (poultry, crops, fish, etc.) from production through processing and regulatory approval. It's designed for a multi-stakeholder ecosystem: farmers, regulators, suppliers, and admins.

## Architecture Principles

### Domain-Driven Route Organization

The API uses **domain-driven separation of concerns** where each route module owns a specific domain boundary with clear responsibility statements:

- **auth_routes.py**: User identity and authorization only—no business logic
- **batch_routes.py**: Physical production groups (flocks, harvest lots, crop cycles)—creation, assignment, status, QR linking
- **lifecycle_routes.py**: Temporal audit trail—vaccinations, medications, measurements, mortality (the critical chain of record)
- **product_routes.py**: Product type definitions (poultry, rice, corn, fish)—not batch instances
- **logistics_routes.py**: Movement and cold chain—transport manifests, temperature, chain of custody
- **processing_routes.py**: Conversion to final product—slaughter, processing facility records, yield, certifications
- **regulatory_routes.py**: Legal compliance—health certificates, export permits, regulator approvals

**Key pattern**: Each module has a docstring declaring what must NOT go there. This prevents domain creep.

### Authentication & Authorization

- **JWT-based** with Bearer token in `Authorization: Bearer <token>` header
- Tokens created via `create_access_token()` with configurable expiry (default 30 min)
- Token blacklist stored in memory (`token_blacklist` set)—switch to Redis in production
- `get_current_user()` dependency validates JWT and retrieves user from DB
- User roles (Enum): FARMER, REGULATOR, SUPPLIER, ADMIN

### Data Layer

- **SQLAlchemy ORM** with declarative base (`app.database.base.Base`)
- Database config via `settings.DATABASE_URL` from environment
- Session management through dependency injection: `Depends(get_db)`
- UUIDs for primary keys (`UUID(as_uuid=True)`)
- Timestamps with timezone support and server-side defaults

### Configuration Management

- Pydantic `BaseSettings` with `.env` file support
- Core settings in `app.core.config.Settings`:
  - `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- All config centralized—no hardcoded values

### Hyperledger Blockchain Integration

AgriTrack synchronizes critical traceability data to Hyperledger Fabric to create an immutable, auditable record of:

- **Farmer compliance history** (certifications passed/failed, regulatory violations)
- **Batch lifecycle events** (disease outbreaks, production issues, quality failures)
- **Chain-of-custody records** (transport, handling, custody transfers)
- **Consumer transparency** (allows consumers to verify product history and farmer reliability)

**Architecture**:

- Blockchain data flows are **one-way**: database → blockchain (no reverse sync needed)
- Critical events trigger blockchain writes (certification failures, illness reports, regulatory actions)
- Blockchain serves as **immutable audit log**—regulatory and consumer-facing records
- Database remains source-of-truth for operational data; blockchain provides transparency

**Key Principle**: Blockchain records are **append-only**. Failed certifications, illnesses, and violations cannot be hidden or modified—they become permanent public record, building consumer trust through transparency.

**Future Integration Points**:

- Event listeners in `lifecycle_routes.py`, `processing_routes.py`, `regulatory_routes.py` trigger blockchain writes
- New `blockchain_routes.py` will expose endpoints for consumers to query farmer/batch history
- Message queue (e.g., RabbitMQ, Kafka) should decouple database writes from blockchain writes for performance

## Development Patterns

### Adding New Routes

1. Create route file in `app/api/routes/`
2. Add responsibility docstring (what goes here / what must NOT)
3. Use `APIRouter(prefix="/path", tags=["category"])` for organization
4. Inject `get_db: Session = Depends(get_db)` for DB access
5. Inject `current_user: User = Depends(get_current_user)` for auth
6. Include router in `app/main.py`: `app.include_router(router)`

### Adding New Models

1. Create in `app/models/` inheriting from `Base`
2. Use descriptive `__tablename__`
3. Use `UUID(as_uuid=True), primary_key=True, default=uuid.uuid4` for IDs
4. Add `created_at` and `updated_at` timestamps with timezone
5. Include `__repr__` for debugging

### Adding New Schemas

1. Create in `app/schemas/` using Pydantic `BaseModel`
2. Use `EmailStr` for emails (requires validation library)
3. Use `field_validator` with `mode='before'` for normalization
4. Separate request and response schemas if needed

## Critical Integration Points

- **Database session**: Always use `get_db` dependency, never create direct connections
- **Authentication**: All protected endpoints must depend on `get_current_user`
- **Token revocation**: Add tokens to `token_blacklist` for logout (migration to Redis needed for distributed systems)
- **Role-based access**: Check `current_user.role` enum values before executing operations

## Key Files by Purpose

| Purpose                           | File                                                                  |
| --------------------------------- | --------------------------------------------------------------------- |
| App entry point                   | [app/main.py](app/main.py)                                            |
| Auth logic & token validation     | [app/api/routes/auth_routes.py](app/api/routes/auth_routes.py)        |
| User model & role enum            | [app/models/user_model.py](app/models/user_model.py)                  |
| Security utilities (hashing, JWT) | [app/core/security.py](app/core/security.py)                          |
| Config & environment              | [app/core/config.py](app/core/config.py)                              |
| Database connection & sessions    | [app/database/session.py](app/database/session.py)                    |
| Hyperledger integration guide     | [docs/HYPERLEDGER_INTEGRATION.md](../docs/HYPERLEDGER_INTEGRATION.md) |

## Common Tasks

### Implement a New Endpoint

```python
# In app/api/routes/domain_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.routes.auth_routes import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/domain", tags=["domain"])

@router.post("/create")
async def create_resource(
    data: CreateResourceSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate user role if needed
    if current_user.role != UserRole.FARMER:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Create and persist
    resource = Resource(**data.dict())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource
```

### Run the Server

```bash
# From project root with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoint Naming Conventions

The API follows RESTful patterns with clear, action-focused naming:

- **POST /auth/register** - Create new user account
- **POST /auth/login** - Authenticate and receive token
- **POST /auth/refresh** - Get new token (authenticated)
- **POST /auth/logout** - Invalidate current token
- **GET /auth/me** - Retrieve authenticated user's info
- **GET /auth/validate-role/{required_role}** - Check if user has specific role
- **PUT /auth/password-change** - Change authenticated user's password
- **POST /auth/password-reset** - Initiate password reset (email-based)

Pattern: All auth endpoints use `/auth` prefix. POST for actions that create/modify, GET for retrieval, PUT for updates. Resource endpoints use `/batch`, `/product`, `/lifecycle`, etc.

## Frontend Integration Guide

### Authentication Flow

1. **Registration**: `POST /auth/register` with `name`, `email`, `password`, `role`

   ```json
   {
     "name": "John Farmer",
     "email": "john@farm.com",
     "password": "secure_password",
     "role": "FARMER"
   }
   ```

   Returns: `{id, email, name, role}`

2. **Login**: `POST /auth/login` with `email`, `password`

   ```json
   {
     "email": "john@farm.com",
     "password": "secure_password"
   }
   ```

   Returns: `{access_token, token_type: "bearer", user_id, role}`

3. **Store Token**: Save `access_token` in localStorage/sessionStorage

4. **Authenticated Requests**: Include in all subsequent requests:

   ```
   Authorization: Bearer <access_token>
   ```

5. **Token Refresh**: `POST /auth/refresh` to get new token before expiry
   Returns: `{access_token, token_type: "bearer"}`

6. **Logout**: `POST /auth/logout` (token automatically blacklisted)

### Error Handling

- **400 Bad Request**: Invalid input (duplicate email, bad format)
- **401 Unauthorized**: Invalid credentials or missing/expired token
- **403 Forbidden**: User lacks required role/permissions
- **500 Server Error**: Database or system issue

All errors return: `{detail: "error message"}`

## Known Limitations & TODO

- Token blacklist is in-memory—scales only to single instance. Migrate to Redis for production
- No role-based endpoint decorators yet—roles checked manually in handlers
- Database uses SQLite by default (`.env` should override for production)
- **[FUTURE]** Implement Alembic for database migrations and schema versioning
- **[FUTURE]** Add health check endpoints for monitoring
- **[FUTURE]** Implement request logging and audit trails
- **[FUTURE - HYPERLEDGER]** Implement Hyperledger Fabric SDK integration for blockchain writes
- **[FUTURE - HYPERLEDGER]** Create event listeners for critical compliance/violation events
- **[FUTURE - HYPERLEDGER]** Implement message queue (RabbitMQ/Kafka) to decouple blockchain writes from API responses
- **[FUTURE - HYPERLEDGER]** Build `blockchain_routes.py` for consumer-facing transparency queries (farmer history, batch certifications)
