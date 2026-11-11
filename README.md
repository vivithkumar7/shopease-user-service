# ShopEase User Management Service

Independent FastAPI microservice for authenticated customer profiles and delivery addresses. Authentication and registration remain in the Authentication Service; this service stores only the Auth Service user ID and profile data.

## Project structure

```text
app/
  core/          Settings and JWT validation
  database/      SQLAlchemy engine and session dependency
  models/        User and address ORM models
  routers/       Profile and address HTTP endpoints
  schemas/       Request validation and response serialization
  services/      Persistence and business rules
alembic/         Database migration environment and revisions
tests/           API tests using an isolated SQLite database
```

## Local setup

Use Python 3.11–3.13 (Python 3.13 is recommended). The pinned `pydantic==2.11.4` depends on `pydantic-core==2.33.2`, which has no Windows wheel for Python 3.14; pip then tries to build Rust code from source. Copy `.env.example` to `.env` (do not commit `.env`) and set strong, private values:

```powershell
Copy-Item .env.example .env
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For subsequent commands, call `.venv\Scripts\python.exe` explicitly or select `.venv\Scripts\python.exe` in VS Code. This avoids accidentally using a different active environment such as a Python 3.14 `(venv)`.

Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` for a local MySQL 8 database. The application database user should not be `root`. Compose uses `MYSQL_APP_USER` (default `shopease_user`) for its non-root application account. `DATABASE_URL` is assembled from these values with SQLAlchemy's URL builder so special characters in passwords are handled correctly.

## Authentication integration

Send `Authorization: Bearer <access-token>` to every profile and address endpoint. The service verifies the JWT signature locally using `JWT_SECRET_KEY` and `JWT_ALGORITHM`, requires an expiry (`exp`), and reads the positive integer Auth Service user ID from `JWT_USER_ID_CLAIM` (default: `sub`). The Authentication Service must issue tokens with these matching settings and claims. Do not send an owner ID in a request body; the service derives ownership only from the verified token.

`AUTH_SERVICE_URL` records the paired Auth Service endpoint; JWT validation in this service is local and does not make a per-request call to it. Coordinate account deactivation with the Authentication Service: `POST /api/users/profile/deactivate` deactivates only the local profile and blocks this service's profile/address operations. It does not revoke tokens or deactivate the Auth Service account. The Auth Service must separately disable that account and revoke or expire its tokens. `DELETE /api/users/profile` permanently deletes the local profile and cascades its addresses only; it never deletes the Auth Service account.

## API endpoints

All routes below require a valid access token.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/users/profile` | Create the current user's profile (201; duplicate returns 409) |
| GET | `/api/users/profile` | Read current user's active profile |
| PUT | `/api/users/profile` | Replace editable profile fields |
| PATCH | `/api/users/profile` | Partially update supplied profile fields |
| POST | `/api/users/profile/deactivate` | Deactivate the local profile |
| DELETE | `/api/users/profile` | Delete the local profile and its addresses (204) |
| POST | `/api/users/addresses` | Add an address |
| GET | `/api/users/addresses` | List current user's addresses |
| GET | `/api/users/addresses/{address_id}` | Get an owned address |
| PUT | `/api/users/addresses/{address_id}` | Replace an owned address |
| PATCH | `/api/users/addresses/{address_id}/default` | Set the owned address as default |
| DELETE | `/api/users/addresses/{address_id}` | Delete an owned address (204) |

Phone numbers are checked for 7–15 digits. Address type must be `Home`, `Office`, or `Other`. Missing/invalid tokens return 401, missing records return 404, cross-user address access returns 403, inactive profiles return 403, and duplicate profiles return 409. Setting a new default clears the previous one in the same transaction; an active user's profile row is locked during this change to serialize concurrent updates on MySQL.

Interactive API documentation is available at `/docs`; liveness endpoint: `/health`.

## Migrations

Create the `shopease_user_db` database and configure the local connection variables, then run:

```powershell
alembic upgrade head
alembic current
```

The initial migration creates the unique `auth_user_id` profile constraint, the profile/address foreign key, and indexes. Roll back one revision with `alembic downgrade -1`.

## Docker Compose

Set `.env` values for the database and JWT settings. Compose creates a non-root application account using `MYSQL_APP_USER` (default `shopease_user`) and `DB_PASSWORD`. Set `MYSQL_ROOT_PASSWORD` to a separate strong value; Compose requires it and does not reuse the application password. Compose starts MySQL 8 with a named persistent volume and health check, then starts the API after MySQL is healthy. Inside Compose, the API connects to MySQL at `mysql:3306`; the host-mapped port is only for local database tools. The API container runs `alembic upgrade head` before Uvicorn.

```powershell
docker compose up --build
```

The API is at `http://localhost:8000` and MySQL is exposed on `localhost:3307` by default. Change `USER_SERVICE_PORT` or `MYSQL_PORT` in `.env` to override these host ports. To stop the containers while preserving database data, run `docker compose down`; `docker compose down -v` also deletes the database volume.

## Tests

Install test-only dependencies and run the API tests:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

Tests use an isolated in-memory SQLite database and cover missing/invalid JWTs (including malformed user-ID claims), profile create/duplicate/read/update/delete and user isolation, phone validation, address ownership and missing records, default-address replacement, local account deactivation, and persisted records. Run `python -m pytest` after installing `requirements-dev.txt`; manual Swagger/Postman checks require a running service and a valid token from the Auth Service. Authorize in Swagger UI at `/docs` and repeat the documented scenarios with Postman. Automated tests do not require or claim a live MySQL, Auth Service, Swagger UI, or Postman run.

## Demo report and screenshots

The [10-page API demo report](demo-output/ShopEase_User_Service_Demo_Report.pdf) includes a Swagger UI screenshot, captured HTTP responses, authorization outcomes, and the final demo database records. Separate images are available for the [Swagger UI](demo-output/swagger-docs.png), [API and database results](demo-output/api-demo-results.png), and [persisted database rows](demo-output/database-snapshot.png).

The report's demonstration used a local FastAPI server, a disposable SQLite database, and locally signed synthetic JWTs. It is not evidence of a live MySQL deployment, Auth Service integration, or Postman run; repeat those integration checks against the configured services before release.