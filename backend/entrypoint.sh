#!/bin/sh
set -e

echo "Menunggu PostgreSQL siap..."
until pg_isready -h db -p 5432 -U user; do
  echo "PostgreSQL belum siap, tunggu 2 detik..."
  sleep 2
done

echo "PostgreSQL siap. Jalankan migrasi database..."
alembic upgrade head

echo "Jalankan server FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000