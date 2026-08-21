#---

# Master Log Progress — Backend SiOslo (Versi Terbaru)

**Tanggal:** 21 Agustus 2026  
**Status:** Docker full stack berjalan, data pasar masuk, korelasi > 0, tetapi `score_breakdown`/`issues` masih null dan blueprint terkadang fallback  
**Author:** Danish (Core Controller) + AI Assistant

---

## 1. Ringkasan Umum

Backend SiOslo berhasil di-deploy menggunakan Docker Compose dengan 3 service:
- `smart_commerce_api` — FastAPI (port 8000)
- `smart_commerce_db` — PostgreSQL 16 (port 5432)
- `smart_commerce_llm` — Ollama (port 11434)

Model fine-tuning `sioslo` berhasil dimuat ke Ollama. Endpoint `/api/v1/analyze` berhasil mengembalikan respons. Data pasar (market trends, demographics, competitor prices) sudah berhasil diimpor ke database Docker, sehingga `keyword_overlap_score` naik dari 0 menjadi 0.2158.

Namun masih ada dua catatan penting:
- Field `score_breakdown` dan `issues` masih `null` karena endpoint `/analyze` kemungkinan masih memakai wrapper lama, bukan `parse_and_validate` langsung.
- Blueprint inovasi terkadang masih berasal dari fallback, bukan LLM murni, karena model membutuhkan waktu inferensi yang lama di CPU.

---

## 2. Timeline & File yang Diubah/Dibuat

### Fase 1: Setup Proyek & Fondasi Backend

**Tujuan:** Membangun struktur aplikasi FastAPI, model database, dan endpoint.

**File dibuat:**
- `backend/app/main.py` — entrypoint FastAPI
- `backend/app/core/config.py` — pydantic-settings untuk `.env`
- `backend/app/core/database.py` — SQLAlchemy engine & session
- `backend/app/models/sales.py` — `SalesReport`, `SalesItem`
- `backend/app/models/market.py` — `MarketTrend`, `Demographic`, `FootTraffic`, `CompetitorPrice`
- `backend/app/schemas/analysis.py` — kontrak API utama (`AnalysisResponse`, dll.)
- `backend/app/schemas/sales.py`, `market.py`, `insight.py` — skema pendukung
- `backend/app/api/v1/api.py` — agregator router
- `backend/app/api/v1/endpoints/sales.py`, `market.py`, `insight.py` — endpoint dasar

**File diubah:**
- `backend/requirements.txt` — daftar library
- `.env.example` — template environment

**Kendala & Solusi:**
- Import `Text`/`DateTime` salah dari `xml` → ganti ke `sqlalchemy`
- Error `No module named 'app'` saat Uvicorn → jalankan dari folder `backend`
- Error Pydantic `Field required` → buat `.env`

---

### Fase 2: Integrasi CSV Parser (Jay)

**Tujuan:** Menghubungkan parser CSV Jay ke endpoint `/analyze`.

**File diubah:**
- `backend/app/services/csv_parser.py` — berisi fungsi asli Jay (`parse_and_validate`) + adapter `parse_sales_csv`
- `backend/app/api/v1/endpoints/analyze.py` — memakai `parse_and_validate` langsung, memetakan `data_health` penuh

**Hasil:** Data health checker berjalan, skor reliabilitas & issues tampil.

---

### Fase 3: Integrasi Correlation Engine (ch3coo)

**Tujuan:** Memasukkan skor korelasi (keyword overlap & price competitiveness) ke respons.

**File diubah:**
- `backend/app/services/correlation_engine.py` — fungsi asli ch3coo (`compute_correlation`)
- `backend/app/api/v1/endpoints/analyze.py` — memanggil `compute_correlation`, membentuk `CorrelationMetric` + `per_product_details`
- `backend/app/schemas/analysis.py` — tambah `PerProductScore`, field `per_product_details`, `score_breakdown`, `issues`

**Hasil:** Endpoint mengembalikan korelasi per produk; skor 0 jika database pasar kosong.

---

### Fase 4: LLM Service (Ollama + Fallback)

**Tujuan:** Menghubungkan FastAPI ke Ollama lokal untuk menghasilkan blueprint inovasi.

**File diubah:**
- `backend/app/services/llm_service.py` — prompt builder, `generate_innovation_blueprint`, `generate_market_insight`, fallback `_simulate_blueprint`

**Kendala & Solusi:**
- Error `LLM_MODEL_NAME` tidak ditemukan → sesuaikan nama field di `config.py`
- Error `generate_market_insight` tidak ada → tambahkan fungsi
- Ganti `requests` → `httpx` (sinkron)

**Hasil:** API bisa memanggil Ollama; jika tidak tersedia, fallback berjalan.

---

### Fase 5: Unit Testing

**Tujuan:** Memastikan endpoint utama dapat diuji.

**File dibuat:**
- `backend/tests/test_analyze_endpoint.py` — skenario sukses, CSV error, missing file

**Kendala & Solusi:**
- Mock ganda diperlukan karena import langsung di `analyze.py`
- Setelah perbaikan, semua test PASS

---

### Fase 6: Scraper Berita & Importer Dataset

**Tujuan:** Menghasilkan data sintetik untuk tabel pasar.

**File dibuat:**
- `backend/scripts/scraper_berita.py` — generate `market_trends.csv`, `demographics.csv`, `competitor_prices.csv`
- `backend/scripts/import_csv.py` — impor CSV ke database

**Kendala & Solusi:**
- Kata kunci terlalu pendek menyebabkan false positive → gunakan word boundary
- Fallback sintetik ditambahkan jika RSS kosong
- Error path `app` → jalankan dengan `python -m scripts.import_csv`

---

### Fase 7: Dockerization Full Stack

**Tujuan:** Membungkus seluruh sistem ke Docker untuk penilaian 100% lokal.

**File dibuat/diubah:**
- `backend/Dockerfile` — base image Python 3.12, install system deps
- `backend/entrypoint.sh` — wait PostgreSQL, init DB, jalankan Uvicorn
- `backend/docker-compose.yml` — service `api`, `db`, `ollama`
- `backend/.dockerignore` — hindari file besar (venv, gguf, csv output)
- `backend/models/ollama-entrypoint.sh` — serve Ollama + buat model
- `backend/models/Modelfile` — definisi model custom dari GGUF
- `.env` — update `DATABASE_URL` & `LLM_ENDPOINT` untuk Docker

**Kendala & Solusi:**
- Error Docker daemon not running → jalankan Docker Desktop
- Build context 5 GB → tambahkan `.dockerignore`
- Numpy version conflict → ganti base image ke `python:3.12-slim`
- Error migrasi `drop_table competitor_prices` → ganti dengan `init_db.py`
- `ModuleNotFoundError: No module named 'app'` → set `ENV PYTHONPATH=/app` di Dockerfile
- Nama model `sioslo-model` invalid → ganti ke `sioslo`, perbaiki CRLF
- GGUF tidak ditemukan → sesuaikan path di Modelfile ke file yang benar (`llama-3-8b.Q4_K_M.gguf`)

---

### Fase 8: Integrasi Model Fine-Tuning

**Tujuan:** Memastikan model `sioslo` ter-load dan merespons.

**File diubah:**
- `backend/models/Modelfile` — `FROM /models/llama-3-8b.Q4_K_M.gguf`
- `.env` — `LLM_MODEL_NAME=sioslo`

**Hasil:**
- `docker logs smart_commerce_llm` menunjukkan model sedang memproses request.
- Endpoint `/analyze` pernah mengembalikan blueprint dari LLM dengan judul "Value Pricing Kopi Susu Aren di Jakarta Timur" — bukti model bekerja.

---

### Fase 9: Import Data Pasar ke Database Docker

**Tujuan:** Mengisi tabel `market_trends`, `demographics`, `competitor_prices` agar korelasi tidak 0.

**Langkah:**
- Salin folder CSV dari host ke container:
  ```powershell
  docker cp app\scripts\output smart_commerce_api:/app/scripts/
  ```
- Jalankan importer di dalam container:
  ```powershell
  docker exec -it smart_commerce_api python -m scripts.import_csv
  ```

**Hasil:**
- ✅ 105 baris `market_trends` diimpor
- ✅ 18 baris `demographics` diimpor
- ✅ 137 baris `competitor_prices` diimpor
- **Total 260 baris data pasar berhasil masuk ke database Docker**

**Dampak:**
- `keyword_overlap_score` pada endpoint `/analyze` naik dari 0 menjadi 0.2158
- `price_competitiveness_score` dapat dihitung karena data kompetitor tersedia

---

### Fase 10: Perbaikan Residual (Sedang Berlangsung)

**Masalah tersisa:**
1. **`score_breakdown` dan `issues` masih `null`**  
   Seharusnya endpoint `/analyze` memakai `parse_and_validate()` langsung dan membangun `DataHealthMetric` dari `health_raw`. Jika masih memakai wrapper `parse_and_validate_csv`, field ini tidak akan terisi.

2. **Blueprint kadang fallback, bukan LLM**  
   Model `sioslo` sudah pernah berhasil, tetapi kadang timeout karena CPU lambat. Perlu pemanasan model atau timeout lebih panjang.

**Langkah perbaikan yang disarankan:**
- Periksa `analyze.py` di host, pastikan menggunakan `parse_and_validate` langsung, bukan `parse_and_validate_csv`.
- Pastikan `csv_parser.py` di host adalah versi final Jay (sudah final sesuai kiriman).
- Perpanjang timeout di `llm_service.py` (sudah 300 detik, bisa tetap).
- Rebuild image API dengan `docker-compose build --no-cache api`.
- Panaskan model sebelum demo dengan request contoh.

---

## 3. Status Saat Ini

| Komponen | Status |
|----------|--------|
| API FastAPI | ✅ Berjalan di port 8000 |
| PostgreSQL | ✅ Sehat di port 5432 |
| Ollama + Model | ✅ Berjalan, model `sioslo` merespons |
| Endpoint `/analyze` | ✅ Berhasil mengembalikan respons |
| Data pasar di Docker | ✅ Sudah diimpor (260 baris) |
| `keyword_overlap_score` | ✅ 0.2158 (tidak lagi 0) |
| `score_breakdown` & `issues` | ⚠️ Masih `null` (perlu penyesuaian `analyze.py`) |
| Blueprint inovasi | ✅ Kadang LLM, kadang fallback (wajar di CPU) |
| Swagger UI | ✅ Akses di `http://localhost:8000/docs` |

---

## 4. Pekerjaan yang Masih Harus Dilakukan

1. **Perbaiki `analyze.py`** agar mengisi `score_breakdown` & `issues`.
2. **Rebuild image API** (`docker-compose build --no-cache api`).
3. **Tes ulang** endpoint `/analyze`.
4. **Panaskan model** sebelum demo (opsional tapi membantu).
5. **Commit & push** seluruh perubahan.
6. **Siapkan proposal & video** untuk submission.

---

## 5. File yang Paling Penting (Cheatsheet)

| File | Fungsi |
|------|--------|
| `app/services/llm_service.py` | Prompt builder + panggil Ollama |
| `app/api/v1/endpoints/analyze.py` | Endpoint utama |
| `app/services/csv_parser.py` | Parser CSV Jay |
| `app/services/correlation_engine.py` | Korelasi ch3coo |
| `docker-compose.yml` | Orkestrasi Docker |
| `models/Modelfile` | Definisi model fine-tuning |
| `scripts/import_csv.py` | Impor data pasar |
| `.env` | Konfigurasi environment |
| `entrypoint.sh` | Startup backend (init DB + Uvicorn) |
| `models/ollama-entrypoint.sh` | Startup Ollama + buat model |

---