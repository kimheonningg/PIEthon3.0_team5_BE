# PIEthon3.0 Medical System Backend

A FastAPI-based medical system backend with PostgreSQL database for managing doctors, patients, and medical notes.

## Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL)
- Git

## Setup Instructions

### 1. Python Environment Setup

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Alternative: Use poetry, conda, or other virtual environment managers
```

### 2. Database Setup

Make sure Docker Desktop is installed and running, then run the setup script:

```bash
# Make setup script executable (if needed)
chmod +x setup.sh

# Run setup script (installs dependencies, starts PostgreSQL, runs migrations)
sh setup.sh
```

The setup script will:
- Install Python dependencies from `requirements.txt`
- Start PostgreSQL and pgAdmin containers via Docker
- Run database migrations with Alembic
- Display connection information

### 3. pgAdmin Setup (Optional)

Access pgAdmin web interface:
1. Open http://localhost:5050 in your browser
2. Login with:
   - Email: `admin@admin.com`
   - Password: `admin`
3. Add PostgreSQL server connection:
   - Host: `postgres` (Docker container name)
   - Port: `5432`
   - Database: `piedb`
   - Username: `pieuser`
   - Password: `piepassword`

### 4. Environment Configuration

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your database configuration (default values should work with Docker setup).

### 5. Run the Application

```bash
python server.py
```

The API will be available at http://localhost:8000

## API Testing

Run the test suite to verify everything is working:

```bash
python test/test_api.py
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **Database Admin**: pgAdmin
- **Containerization**: Docker & Docker Compose
- **Migrations**: Alembic
- **Testing**: Custom async test suite

## Project Structure

```
PIEthon3.0_team5_BE/
├── core/
│   ├── models/          # Pydantic request/response models
│   ├── manage_funcs/    # Business logic for patients & notes
│   ├── auth.py          # Authentication logic
│   └── db.py            # Database configuration
├── alembic/             # Database migrations
├── test/                # API test suite
├── docker-compose.yml   # PostgreSQL & pgAdmin containers
├── server.py            # FastAPI application
└── requirements.txt     # Python dependencies
```

## Database Schema

### Users (Doctors)
- `user_id` (Primary Key): Doctor's unique identifier
- `email`: Doctor's email address
- `licence_num`: Medical license number
- `phone_num`, `first_name`, `last_name`: Personal information
- `password`: Hashed password

### Patients
- `patient_id` (Primary Key): Patient's unique identifier
- `phone_num`, `first_name`, `last_name`: Personal information
- Many-to-many relationship with doctors

### Notes (Medical Records)
- `note_id` (Primary Key): Note's unique identifier
- `patient_id` (Foreign Key): References patient
- `doctor_id` (Foreign Key): References doctor
- `title`, `content`: Note information
- `note_type`: Category of medical note

## Key Features

- 🔐 **JWT Authentication**: Secure doctor login system
- 👥 **Patient Management**: Create and assign patients to doctors
- 📝 **Medical Notes**: Create, read, update medical records
- 🔗 **Relationships**: Proper database relationships between doctors, patients, and notes
- 🧪 **Comprehensive Testing**: Full API test suite
- 🐳 **Docker Ready**: Easy database setup with Docker

## Notes

- Only doctors can register accounts (patients are created by doctors)
- Patients are identified by `patientId`, doctors by `userId`
- All medical data is protected by JWT authentication
- Database uses proper relational design with foreign keys and constraints

## Troubleshooting

If you encounter issues:

1. **Database connection errors**: Ensure Docker Desktop is running and containers are started
2. **Migration errors**: Try `alembic downgrade base` then `alembic upgrade head`
3. **Permission errors**: Run `chmod +x setup.sh` before executing
4. **Port conflicts**: Check if ports 5432, 5050, or 8000 are already in use