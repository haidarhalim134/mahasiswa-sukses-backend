# Mahasiswa Sukses Backend

A FastAPI-based backend application for the Mahasiswa Sukses project, using SQLAlchemy for database management, Alembic for migrations, and Supabase for additional services.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database (or compatible)
- Supabase account and project

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd mahasiswa-sukses-backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory based on .env.example file. Replace the values with your actual database connection string and Supabase credentials.

## Running the Project

1. Ensure your virtual environment is activated.

2. Start the development server:
   ```
   uvicorn app.main:app --reload
   ```

3. The API will be available at `http://localhost:8000`

4. Access the interactive API documentation at `http://localhost:8000/docs`

## Database Migrations

This project uses Alembic for database schema migrations.

### Creating a New Migration

When you make changes to your database models (e.g., in `app/users/models.py`), create a new migration:

```
alembic revision --autogenerate -m "Description of changes"
```

This will generate a new migration file in `alembic/versions/`.

### Applying Migrations

To apply all pending migrations to your database:

```
alembic upgrade head
```

To rollback to a previous migration:

```
alembic downgrade <revision-id>
```

### Checking Migration Status

To see the current migration status:

```
alembic current
```

To see all available migrations:

```
alembic history
```