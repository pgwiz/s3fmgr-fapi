set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python scripts/migrate.py

# Run database seeding
echo "Seeding database..."
python scripts/seed.py

echo "Build complete."
