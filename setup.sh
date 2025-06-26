#!/bin/bash

set -e  # Exit on any error

echo "Setting up PIEthon3.0 Medical System..."
echo

echo "Installing dependencies..."
pip install -r requirements.txt
echo "Dependencies installed"
echo

echo "Stopping and cleaning up existing containers..."
docker compose down -v  # This removes volumes too
echo "Containers stopped and volumes cleared"
echo

echo "Starting fresh PostgreSQL container..."
docker compose up -d
echo "PostgreSQL container started"
echo

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 15  # Increased wait time for fresh container

# Check if PostgreSQL is accepting connections
echo "Checking PostgreSQL connection..."
until docker compose exec postgres-db pg_isready -U admin -d postgres > /dev/null 2>&1; do
    echo "   Still waiting for PostgreSQL..."
    sleep 3
done
echo "PostgreSQL is ready"
echo

echo "Running database migrations..."
# For a fresh database, this should work without issues
if alembic upgrade head; then
    echo "Database migrations completed successfully"
else
    echo "Migration failed. Checking if tables exist..."
    # Check if tables exist and sync if needed
    TABLE_COUNT=$(docker compose exec -T postgres-db psql -U admin -d postgres -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$TABLE_COUNT" -gt "0" ]; then
        echo "Found $TABLE_COUNT tables. Syncing migration state..."
        alembic stamp head
        echo "Migration state synchronized"
    else
        echo "No tables found but migration failed. Please check your migration files."
        exit 1
    fi
fi
echo

echo "Setup complete! You can now:"
echo "   • Start the server: python server.py"
echo "   • Access pgAdmin: http://localhost:8888"
echo "   • View API docs: http://localhost:8000/docs"
echo
echo "pgAdmin credentials:"
echo "   • Email: admin@example.com"
echo "   • Password: admin"
echo
echo "Add new server in pgAdmin with following configurations:"
echo "   • Host name/address: piethon-pg"
echo "   • Port: 5432"
echo "   • Database: postgres"
echo "   • Username: admin"
echo "   • Password: 123456"
echo
echo "After adding server, check tables in Servers > server_name > Databases > postgres > Schemas > Tables > table_name"
echo "Right click table_name and view/edit data interactively"