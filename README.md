# Mistri Nepal Backend

Mistri Nepal Backend is a REST API for a platform that connects customers with
skilled service professionals. It provides the server-side foundation for user
accounts, authentication, professional profiles and applications, skills,
bookings, file uploads, and payment-related integrations.

## Why this project?

Finding a reliable professional for home and local services can be difficult.
Mistri Nepal is intended to make that process easier by providing a single
backend for:

- Customer and professional account management
- Secure registration and login with JWT access and refresh tokens
- Professional applications and skill management
- Booking workflows and payment status tracking
- File and image uploads through Cloudinary
- Role-based authorization and administrative operations
- eSewa payment configuration and Firebase notification support

## Tools and technologies

- **Python 3.13+**
- **FastAPI** for the REST API and automatic OpenAPI documentation
- **Uvicorn** for serving the application
- **Pydantic Settings** for environment-based configuration and validation
- **SQLAlchemy 2.0** with async sessions and **asyncpg**
- **PostgreSQL** as the primary database
- **Alembic** for database migrations
- **JWT, PyJWT, Argon2, and Passlib** for authentication and password security
- **Cloudinary** for media storage
- **eSewa** payment integration configuration
- **Firebase** configuration for push notifications
- **Redis** configuration for supporting application services
- **uv** for dependency and virtual-environment management

## Project structure

```text
app/
â”œâ”€â”€ main.py                         # FastAPI application entry point
â”œâ”€â”€ common/                         # Shared enums, schemas, and utilities
â”œâ”€â”€ core/                           # Configuration, database, security, and logging
â””â”€â”€ modules/
    â”œâ”€â”€ auth/                       # Registration and login
    â”œâ”€â”€ booking/                    # Booking models and API logic
    â”œâ”€â”€ file/                       # File upload models and API logic
    â”œâ”€â”€ professional_applications/  # Professional application workflows
    â”œâ”€â”€ professionals/              # Professional profiles
    â”œâ”€â”€ skills/                     # Skill management
    â””â”€â”€ users/                      # User management
alembic/
â””â”€â”€ versions/                       # Database migration revisions
```

## Prerequisites

Install the following before starting:

- Python 3.13 or newer
- PostgreSQL
- [uv](https://docs.astral.sh/uv/)
- A Cloudinary account if media uploads are required
- Firebase credentials if push notifications are required
- eSewa merchant credentials if payment processing is required

## Running locally

### 1. Clone the repository

```powershell
git clone <repository-url>
cd Mistri-Nepal-Backend
```

### 2. Install dependencies

The project is configured for `uv` and requires Python 3.13 or newer:

```powershell
uv sync
```

This creates or updates the project virtual environment and installs the
locked dependencies from `uv.lock`.

### 3. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update `.env` with values for your local PostgreSQL database and integrations.
At minimum, configure the database credentials, `SECRET_KEY`, and the required
Cloudinary variables. For the async SQLAlchemy engine, `DATABASE_URL` should
use an async PostgreSQL driver, for example:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/mistri_nepal_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mistri_nepal_db
SECRET_KEY=replace-with-a-long-random-secret
```

Do not commit `.env`, Firebase service-account files, or production secrets.

### 4. Create the database and run migrations

Create the `mistri_nepal_db` database in PostgreSQL, then apply the schema:

```powershell
uv run alembic upgrade head
```

### 5. Start the API

```powershell
uv run uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive documentation is
available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redocs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

The configured API version prefix is `/api/v1`.

## Database migrations

After changing SQLAlchemy models, generate a migration and review it before
applying it:

```powershell
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
```

To roll back the latest migration:

```powershell
uv run alembic downgrade -1
```

## Configuration notes

Configuration is loaded from `.env` by
`app/core/config/config.py`. The application also reads settings for:

- JWT expiration and signing algorithm
- CORS allowed origins
- Upload size and upload directory
- Redis
- Firebase credentials
- Cloudinary
- eSewa

Use environment-specific values in development, staging, and production.