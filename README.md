# Asset Management API

A REST API for managing internet-facing security assets — domains, subdomains,
IP addresses, services, certificates, and technologies — with deduplication,
lifecycle tracking, relationship graphs, and multi-tenant isolation.

Built as part of the Buguard DarkAtlas internship task (Track A — Backend Engineering).

## Tech stack

- Python 3.11+
- FastAPI + Pydantic v2
- PostgreSQL 16 (via SQLAlchemy 2 + Alembic)
- JWT authentication (python-jose)
- Docker + Docker Compose

---

## Quick start

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd asset-management
cp .env.example .env
```

Edit `.env` and set a strong `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Run with Docker (recommended)

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 3. Run locally (without Docker)

```bash
pip install -r requirements.txt
# ensure PostgreSQL is running and DATABASE_URL in .env is correct
alembic upgrade head
uvicorn main:app --reload
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | `postgresql://postgres:postgres@localhost:5432/assetdb` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | **yes** | — | Secret for signing JWTs. App will refuse to start without this. |
| `JWT_ALGORITHM` | no | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | no | `10080` (7 days) | Refresh token lifetime |

---

## Running tests

Tests use SQLite in-memory — no running Postgres required.

```bash
pip install -r requirements.txt
pytest app/tests/ -v
```

---

## API overview

Full interactive docs are available at `/docs` (Swagger UI) after starting the server.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register a new user (creates an organization) |
| POST | `/api/v1/auth/login` | Login, returns access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh an access token |

### Assets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/assets/` | List assets (filter, sort, paginate) |
| POST | `/api/v1/assets/` | Create a single asset |
| GET | `/api/v1/assets/{id}` | Get asset by ID |
| PUT | `/api/v1/assets/{id}` | Update asset |
| DELETE | `/api/v1/assets/{id}` | Soft-delete (archives) an asset |
| PATCH | `/api/v1/assets/{id}/stale` | Mark asset as stale |
| POST | `/api/v1/assets/import` | Bulk import with deduplication |
| GET | `/api/v1/assets/{id}/graph` | Asset + all related assets |
| GET | `/api/v1/assets/{id}/relationships` | List an asset's relationships |

### Relationships

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/relationships` | Create a relationship between two assets |

**List query parameters:** `type`, `status`, `tag`, `search` (value contains), `sort` (value/status/first_seen/last_seen), `order` (asc/desc), `skip`, `limit` (default 50, max 500).

---

## Design decisions & assumptions

**Multi-tenancy:** Every user registers their own organization. All assets and relationships are scoped to `organization_id` — one tenant's data is never accessible to another. The uniqueness constraint on assets is `(type, value, organization_id)`.

**Deduplication:** An asset is identified by `(type, value, organization_id)`. Re-importing the same asset updates `last_seen`, merges tags as a sorted set union, and shallow-merges `extra_data` (incoming keys win on conflict). A stale asset that reappears is automatically set back to active.

**Soft deletes:** DELETE sets `status = archived`. Archived assets are excluded from all list and GET responses. This preserves history and relationship integrity.

**`extra_data` vs `metadata`:** The spec uses `metadata` but this is a reserved word in SQLAlchemy's `Base`, so the column is named `extra_data`. The API schema field and JSON key are also `extra_data` for consistency.

**Conflicting data from two sources:** The merge strategy is last-write-wins for scalar fields, union for tags, and shallow-merge for `extra_data`. This is documented here rather than silently applied.

**Malformed records in bulk import:** Each record in a bulk import is wrapped in a try/except. A bad record increments the `failed` counter and appends an error message; the rest of the batch continues.

**Pagination defaults:** `limit` defaults to 50 (not 100) to prevent accidentally returning a large inventory in one shot. Maximum is 500.