# Cara Menjalankan SiOslo Backend dengan Docker

Panduan ini untuk menjalankan seluruh stack backend (FastAPI + PostgreSQL + Ollama) secara 100% lokal menggunakan Docker Compose.

## 1. Prasyarat

- Docker Desktop sudah terinstall dan berjalan (untuk Windows/Mac).
- Tidak perlu install Python/PostgreSQL/Ollama secara manual.

## 2. Struktur Service

| Service | Container Name | Port |
|---------|---------------|------|
| FastAPI (backend) | `smart_commerce_api` | 8000 |
| PostgreSQL | `smart_commerce_db` | 5432 |
| Ollama (LLM) | `smart_commerce_llm` | 11434 |

## 3. Langkah Menjalankan

1. Buka terminal di folder `backend`.
2. Pastikan file `.env` sudah ada dan berisi:
   ```env
   DATABASE_URL=postgresql://user:password@db:5432/smart_commerce
   LLM_ENDPOINT=http://ollama:11434/api/generate
   LLM_MODEL_NAME=sioslo
Jalankan build & start:

powershell
docker-compose up --build
atau jika ingin berjalan di background:

powershell
docker-compose up -d --build
Tunggu proses build selesai. Build pertama butuh waktu cukup lama karena mengunduh base image dan library.

Setelah semua container berjalan, cek status:

powershell
docker ps
Pastikan tiga container statusnya Up.

4. Akses Aplikasi
Swagger UI: http://localhost:8000/docs

Health check: http://localhost:8000/health

API Utama: POST http://localhost:8000/api/v1/analyze/

5. Mengimpor Data Pasar
Data pasar (tren, demografi, harga kompetitor) sudah disediakan dalam bentuk CSV di app/scripts/output/. Untuk mengimpor ke database di dalam container:

powershell
# Salin folder CSV ke container
docker cp app\scripts\output smart_commerce_api:/app/scripts/

# Jalankan importer
docker exec -it smart_commerce_api python -m scripts.import_csv
6. Pemanasan Model (Supaya Respons LLM Lebih Cepat)
Sebelum demo, lakukan request pemanasan agar model ter-load di RAM:

powershell
docker exec -it smart_commerce_api python -c "import httpx; httpx.post('http://ollama:11434/api/generate', json={'model':'sioslo','prompt':'tes','stream':False}, timeout=300)"
7. Troubleshooting
Semua container restart terus
Cek log masing-masing:

powershell
docker logs smart_commerce_api --tail 50
docker logs smart_commerce_db --tail 50
docker logs smart_commerce_llm --tail 50
Port sudah dipakai
Ubah mapping port di docker-compose.yml, misal 8000:8000 menjadi 8001:8000.

File .sh error Illegal option -
Ubah line ending ke LF (bukan CRLF) di VS Code, atau jalankan:

powershell
(Get-Content entrypoint.sh -Raw) -replace "`r", "" | Set-Content entrypoint.sh -NoNewline
Model tidak ditemukan
Pastikan model sudah dibuat:

powershell
docker exec -it smart_commerce_llm ollama list
Jika belum, buat:

powershell
docker exec -it smart_commerce_llm ollama create sioslo -f /models/Modelfile
8. Menghentikan Semua Service
powershell
docker-compose down
Untuk menghapus volume database (data hilang):

powershell
docker-compose down -v