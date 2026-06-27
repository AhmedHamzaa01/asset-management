# Asset Management API

[![CI](https://github.com/your-username/asset-management/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/asset-management/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

A production-ready REST API for tracking, categorizing, and managing digital assets (domains, IP addresses, subdomains, certificates, services, and technologies) within a multi-tenant organization structure. Built with FastAPI and clean architecture principles.

---

## Overview

Security and infrastructure teams accumulate large inventories of digital assets across scans, imports, and manual entry. This API provides a structured backend to:

- **Ingest** assets from external scanners or manual input — individually or in bulk
- **Track** asset lifecycle (active → stale → archived) with automatic re-activation on re-discovery
- **Query** assets with rich filtering, search, pagination, and sorting
- **Map** relationships between assets and retrieve graph views of how they connect
- **Monitor** certificate expiry with automatic status enrichment (`valid`, `expiring_soon`, `expired`)
- **Isolate** all data per organization using UUID-scoped multi-tenancy enforced at every query layer

---

## Features

- **JWT Authentication** — Access + refresh token pair issued on login; refresh endpoint extends sessions without re-login
- **Multi-tenant data isolation** — Every asset, relationship, and query is scoped to the authenticated user's `organization_id`; no cross-org data leakage is possible
- **Bulk import with partial success** — `POST /assets/import` processes batches record-by-record; one bad record never aborts the whole batch; returns `207 Multi-Status` on partial failure with per-row error detail
- **Upsert-on-reimport** — Re-importing an existing asset merges tags (de-duplicated, sorted) and updates `last_seen` rather than creating a duplicate; stale assets are automatically re-activated
- **Soft delete** — `DELETE /assets/{id}` archives the asset (status → `archived`) instead of removing it from the database; archived assets are invisible to list and get endpoints
- **Asset lifecycle controls** — Dedicated `PATCH /assets/{id}/stale` endpoint for marking stale; `PUT /assets/{id}` intentionally prevents status changes to avoid accidental overwrites
- **Certificate status enrichment** — Certificates carrying an `expires` field in `extra_data` are automatically annotated with `certificate_status` (`valid`, `expiring_soon` within 30 days, `expired`) on every read
- **Relationship graph** — Link assets with typed relationships and retrieve a graph view (`GET /assets/{id}/graph`) showing all directly related assets in a single query
- **Paginated, filterable listing** — Filter by type, status, tag, and free-text search; sort by value, status, first\_seen, or last\_seen; paginated with total count returned
- **Flexible metadata** — `tags` (PostgreSQL ARRAY) and `extra_data` (JSON column) allow arbitrary enrichment without schema changes
- **Database migrations** — Alembic tracks all schema changes with versioned migration files and full downgrade support
- **Containerized stack** — `docker-compose.yml` brings up the API, PostgreSQL, and a dedicated test database with a single command
- **GitHub Actions CI** — Tests run automatically on every push and pull request against a real PostgreSQL 16 instance (not a mock)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI 0.104 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Migrations | Alembic 1.12 |
| Auth | JWT via `python-jose`, bcrypt via `passlib` |
| Validation | Pydantic v2 |
| Server | Uvicorn (ASGI) |
| Testing | pytest, pytest-asyncio, httpx / FastAPI TestClient |
| Containerization | Docker, Docker Compose |
| CI | GitHub Actions |

---

## Architecture & Project Structure

The codebase follows a **clean / layered architecture** with strict separation of concerns. No layer reaches past its immediate neighbor.

```
asset-management/
├── main.py                         # App entry point — wires FastAPI, exception handlers, router
├── Dockerfile                      # Single-stage Python 3.11-slim image
├── docker-compose.yml              # API + postgres + postgres-test services
├── alembic.ini                     # Alembic configuration
├── alembic/
│   ├── env.py                      # Migration environment (reads DATABASE_URL from .env)
│   └── versions/                   # Versioned migration files
│       ├── d347d8e39e65_*.py       # Initial schema — users, assets, relationships
│       └── 94aecb2974d2_*.py       # FK constraints + performance indexes
├── requirements.txt
├── env.example                     # Required environment variables template
└── app/
    ├── api/
    │   ├── deps.py                 # FastAPI dependency injection — services, current user
    │   └── v1/
    │       ├── endpoints/
    │       │   ├── assets.py       # CRUD + import + stale + graph endpoints
    │       │   ├── auth.py         # Register, login, refresh
    │       │   └── relationships.py
    │       └── schemas/
    │           ├── asset.py        # AssetCreate, AssetUpdate, AssetResponse, Paginated
    │           ├── auth.py         # LoginRequest, RegisterRequest, TokenResponse
    │           ├── graph.py        # AssetGraphResponse
    │           ├── import_schema.py # RawAssetRecord (lenient), BulkImportRequest
    │           └── relationship.py
    ├── core/
    │   ├── config.py               # Settings dataclass — reads from .env; fails fast on bad config
    │   ├── security.py             # JWT encode/decode, bcrypt hash/verify, 72-byte truncation guard
    │   └── exceptions.py           # Domain exceptions: NotFoundError, ConflictError, UnauthorizedError
    ├── domain/
    │   ├── enums.py                # AssetType, AssetStatus enums
    │   └── models/
    │       ├── asset.py            # Asset SQLAlchemy model
    │       ├── relationship.py     # Relationship model (source → target with type)
    │       └── user.py             # User model (UUID PK, organization_id)
    ├── infrastructure/
    │   └── database.py             # SQLAlchemy engine, session factory, Base, get_db()
    ├── repositories/
    │   ├── asset_repository.py     # DB queries for assets — filtering, sorting, upsert logic
    │   ├── relationship_repository.py # Relationship queries + graph traversal
    │   └── user_repository.py      # User lookup by email / ID
    ├── services/
    │   ├── asset_service.py        # Business logic — bulk import, upsert, cert enrichment, soft delete
    │   ├── auth_service.py         # Register, login, token refresh
    │   └── relationship_service.py # Create + list relationships with duplicate guard
    └── tests/
        ├── conftest.py             # Fixtures: isolated test DB, test user, auth headers, TestClient
        ├── test_assets.py          # ~20 tests: CRUD, filtering, pagination, lifecycle, auth guards
        ├── test_relationships.py   # Relationship creation, duplicate rejection, graph retrieval
        └── test_import.py          # Bulk import: insert, upsert, tag merge, error handling, auth
```

**Key design decisions:**

- **Repository pattern** separates all SQL from business logic; services never touch `db` directly
- **Dependency injection via `Annotated` type aliases** (`CurrentUserDep`, `AssetServiceDep`) keeps endpoint signatures clean and testable
- **Custom domain exceptions** (`NotFoundError`, `ConflictError`, `UnauthorizedError`) are caught by global exception handlers and mapped to HTTP status codes — business logic never imports FastAPI
- **Fail-fast config** — the app exits at startup with a clear error message if `JWT_SECRET_KEY` is still set to `"change-me"`
- **Lenient bulk import schema** (`RawAssetRecord`) accepts `Any` types and validates per-record inside the service, preventing a single bad row from causing a 422 rejection of the whole batch
- **Organization-scoped tokens** — the JWT payload embeds `organization_id` alongside `sub`; `get_current_user` validates both, preventing token reuse across organizations

---

## Installation

**Prerequisites:** Python 3.11+, Docker, and Docker Compose

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/your-username/asset-management.git
cd asset-management

cp env.example .env
# Edit .env and set a real JWT_SECRET_KEY

docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### Option B — Local (virtualenv)

```bash
git clone https://github.com/your-username/asset-management.git
cd asset-management
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp env.example .env
# Edit .env — set DATABASE_URL and JWT_SECRET_KEY

# Start PostgreSQL (e.g. via Docker)
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=assetdb \
  postgres:16

# Apply migrations
alembic upgrade head

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Usage

Once running, the interactive API docs are available at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health check:** `http://localhost:8000/health`

**Quick start:**

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "securepassword"}'

# 2. Login — returns access_token and refresh_token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "securepassword"}'

# 3. Use the token
TOKEN="<access_token from login>"

# 4. Create an asset
curl -X POST http://localhost:8000/api/v1/assets/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "domain", "value": "example.com", "source": "manual"}'

# 5. Bulk import
curl -X POST http://localhost:8000/api/v1/assets/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"assets": [{"type": "ip_address", "value": "1.2.3.4"}, {"type": "subdomain", "value": "api.example.com"}]}'
```

---

## Environment Variables

Copy `env.example` to `.env` and configure the following:

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql://postgres:postgres@localhost:5432/assetdb` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | **Yes** | _(none — app exits if unset or `"change-me"`)_ | Secret used to sign JWTs. Generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | No | `10080` (7 days) | Refresh token TTL |
| `PROJECT_NAME` | No | `Asset Management API` | Displayed in API docs title |
| `API_V1_PREFIX` | No | `/api/v1` | API route prefix |

---

## API Endpoints

All routes (except auth) require `Authorization: Bearer <access_token>`.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user; auto-creates a UUID organization |
| `POST` | `/api/v1/auth/login` | Login; returns `access_token` + `refresh_token` |
| `POST` | `/api/v1/auth/refresh` | Exchange a refresh token for a new token pair |

### Assets

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/assets/` | Create a single asset (upserts on type+value collision) |
| `POST` | `/api/v1/assets/import` | Bulk import; partial failures return `207` with per-row errors |
| `GET` | `/api/v1/assets/` | List assets with filtering, search, pagination, sorting |
| `GET` | `/api/v1/assets/{id}` | Get a single asset by ID |
| `PUT` | `/api/v1/assets/{id}` | Update `source`, `tags`, or `extra_data` |
| `DELETE` | `/api/v1/assets/{id}` | Soft-delete (archives asset; hides from all reads) |
| `PATCH` | `/api/v1/assets/{id}/stale` | Mark asset as stale |
| `GET` | `/api/v1/assets/{id}/graph` | Retrieve asset with all directly related assets |

**Query parameters for `GET /api/v1/assets/`:**

| Param | Type | Description |
|---|---|---|
| `type` | enum | Filter by `domain`, `subdomain`, `ip_address`, `service`, `certificate`, `technology` |
| `status` | enum | Filter by `active`, `stale` (archived assets are always excluded unless queried directly) |
| `tag` | string | Filter assets that include this tag |
| `search` | string | Substring match on `value` |
| `sort` | string | Column to sort by: `value`, `status`, `first_seen`, `last_seen` |
| `order` | string | `asc` or `desc` (default: `desc`) |
| `skip` | int | Pagination offset (default: `0`) |
| `limit` | int | Page size, max `500` (default: `50`) |

### Relationships

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/relationships` | Create a typed relationship between two assets |
| `GET` | `/api/v1/assets/{id}/relationships` | List all relationships for an asset |

---

## Database Schema

Three tables, all organization-scoped:

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` PK | Auto-generated on registration |
| `email` | `VARCHAR(255)` | Unique |
| `hashed_password` | `VARCHAR(255)` | bcrypt |
| `organization_id` | `UUID` | Auto-generated on registration; scopes all data |

### `assets`
| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `type` | `ENUM` | `domain`, `subdomain`, `ip_address`, `service`, `certificate`, `technology` |
| `value` | `VARCHAR(500)` | The asset value (hostname, IP, CN, etc.) |
| `status` | `ENUM` | `active`, `stale`, `archived` |
| `first_seen` | `TIMESTAMPTZ` | Set on creation |
| `last_seen` | `TIMESTAMPTZ` | Updated on every upsert |
| `source` | `VARCHAR(100)` | Originating scanner or `"import"` |
| `tags` | `TEXT[]` | PostgreSQL array for multi-value tagging |
| `extra_data` | `JSON` | Arbitrary enrichment metadata |
| `organization_id` | `UUID` | FK to user's organization |

Unique constraint: `(type, value, organization_id)` — prevents duplicates per org.

### `asset_relationships`
| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER` PK | Auto-increment |
| `source_asset_id` | `INTEGER` | FK → `assets.id` (CASCADE DELETE) |
| `target_asset_id` | `INTEGER` | FK → `assets.id` (CASCADE DELETE) |
| `relationship_type` | `VARCHAR(100)` | e.g. `"subdomain_of"`, `"hosted_on"` |
| `organization_id` | `UUID` | Enforces cross-org isolation |

Unique constraint: `(source_asset_id, target_asset_id, relationship_type, organization_id)`.

---

## Running Tests

```bash
# Option A — Docker Compose (spins up a dedicated test DB)
docker-compose run test

# Option B — local (requires postgres-test on port 5433)
docker-compose up -d postgres-test
pytest app/tests/ -v
```

The test suite uses a real PostgreSQL database (not SQLite mocks). Each test function gets a fresh schema via `autouse` fixtures that call `create_all` / `drop_all`.

**Test coverage includes:**

- Full CRUD lifecycle for assets
- Soft delete and archive visibility rules
- Status field protection on `PUT` (cannot mutate via update endpoint)
- Bulk import: insert, upsert, tag merge, idempotency, malformed-record handling, `207` partial success
- Certificate status enrichment (`expired`, `expiring_soon`, `valid`)
- Stale-to-active revival on re-import
- Relationship creation, duplicate rejection, listing, and graph traversal
- Auth guards: all protected endpoints return `401` without a valid token

---

## Current Status

| Feature | Status |
|---|---|
| Core REST API | ✅ Complete |
| JWT Authentication | ✅ Complete |
| Multi-tenancy | ✅ Complete |
| Bulk import | ✅ Complete |
| Asset lifecycle management | ✅ Complete |
| Certificate status enrichment | ✅ Complete |
| Relationship graph | ✅ Complete |
| Database migrations (Alembic) | ✅ Complete |
| Docker + Docker Compose | ✅ Complete |
| GitHub Actions CI | ✅ Complete |
| Cloud deployment (AWS/GCP/etc.) | 🔲 Not yet configured |
| Frontend / UI | 🔲 Not included |
| Rate limiting | 🔲 Not yet implemented |
| Role-based access control | 🔲 Not yet implemented |

---

## Challenges Solved

**Bulk import partial failure handling.** A naive implementation would 422 the entire request if any record failed validation. Instead, `POST /assets/import` uses a lenient `RawAssetRecord` schema (fields typed as `Any`) and validates each record individually inside the service layer. One bad record logs an error and increments the `failed` counter; the rest continue processing. The response returns `207 Multi-Status` only when failures exist, with per-row error messages.

**Stale asset revival.** When a stale asset is re-imported, it should become active again rather than staying stale or creating a duplicate. The upsert path in `AssetService._upsert_asset` explicitly checks the current status and flips it back to `active`, mimicking real-world scanner re-discovery behavior.

**bcrypt 72-byte truncation.** bcrypt silently truncates passwords longer than 72 bytes, which means passwords differing only beyond that length would hash identically. `security.py` explicitly truncates to 72 bytes before hashing and verification, making the behavior explicit and consistent across passlib/bcrypt version changes.

**Organization-scoped token validation.** JWTs embed both `sub` (user ID) and `organization_id`. The `get_current_user` dependency validates that the `organization_id` in the token matches the one stored in the database for that user, preventing a valid token from being reused across organizations even if the signature is valid.

**Test database isolation.** Every test function gets a clean schema via `autouse` pytest fixtures that call `Base.metadata.create_all` before and `drop_all` after. This ensures zero state leakage between tests without requiring a transaction rollback strategy.

---

## What I Learned

- **Layered architecture in Python** — structuring a FastAPI project into domain, infrastructure, repository, and service layers makes business logic testable in isolation and keeps endpoints thin
- **JWT dual-token pattern** — issuing short-lived access tokens and longer-lived refresh tokens, with token type validation on decode, prevents misuse of refresh tokens as access tokens
- **Pydantic v2 `model_validate` override** — extending the default validation method to inject computed fields (certificate status) from related data without changing the database schema
- **Alembic schema versioning** — writing upgrade and downgrade paths for every migration and structuring the env to pick up the DATABASE_URL from the environment rather than hardcoding it
- **PostgreSQL-specific column types in SQLAlchemy** — using `ARRAY(String)` for multi-value tags and `UUID(as_uuid=True)` for type-safe UUIDs; understanding how Alembic handles dialect-specific types in autogenerated migrations
- **Real-database testing** — running pytest against a real PostgreSQL instance (not SQLite) catches type coercion issues, constraint violations, and ARRAY query behavior that in-memory databases would mask


## Why This Project Stands Out

Most portfolio REST APIs implement the same todo-list CRUD. This project tackles real engineering concerns found in security tooling and SaaS backends:

- Multi-tenant data isolation enforced at the query layer — not just a `WHERE` clause bolted on
- A bulk import endpoint that handles partial failure gracefully and returns structured error detail per record
- Domain-driven lifecycle state machine for assets, with intentional API surface design (status changes are gated behind dedicated endpoints, not a generic update)
- Automatic enrichment (certificate status) computed at read time from JSON metadata — extensible without schema changes
- Graph query capability for relationship traversal
- Integration tests against a real PostgreSQL instance in CI, catching dialect-specific behavior that SQLite would miss

---

## Repository Structure (tree)

```
asset-management/
├── .github/workflows/ci.yml
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── d347d8e39e65_*.py   (initial schema)
│       └── 94aecb2974d2_*.py   (FK constraints + indexes)
├── app/
│   ├── api/v1/
│   │   ├── endpoints/          (assets, auth, relationships)
│   │   └── schemas/            (Pydantic request/response models)
│   ├── core/                   (config, security, exceptions)
│   ├── domain/                 (SQLAlchemy models, enums)
│   ├── infrastructure/         (database engine, session)
│   ├── repositories/           (data access layer)
│   ├── services/               (business logic layer)
│   └── tests/                  (pytest integration tests)
├── docker-compose.yml
├── Dockerfile
├── env.example
├── main.py
└── requirements.txt
```

## License

No license file is currently included in this repository. If you intend to open-source this project, consider adding an MIT or Apache 2.0 license.