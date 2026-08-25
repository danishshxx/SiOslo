# SiOslo - Market-Driven R&D Buddy

**Repository for Compfest UI 2026 - AIC (AI Innovation Challenge)**

SiOslo is a locally-run, AI-powered market research and product decision tool built for product-based SMBs (Small and Medium-sized Businesses). It helps business owners turn their own historical sales CSV data into grounded product innovation decisions — without sending any data to the cloud.

The system processes sales data through a deterministic health-check pipeline, correlates it against static local market snapshots, and runs a fine-tuned local Llama 3 model (via Ollama) to generate Innovation Blueprint recommendations with pricing guidance and ready-to-send WhatsApp copy text.

---

## Team - Kembali Ke Solo

| Name |
|------|
| Muhammad Danish Abrisam |
| Hudzaifah |
| Farras Dary Santosa |
| Andi Rifanti Fitrah Riwan Lewa | 
| Vallencia Febriana |

---

## What This Repository Contains

This is a monorepo with two main components that must run simultaneously:

### Backend (`/backend`)

A FastAPI application that exposes a single primary endpoint: `POST /api/v1/analyze/`.

When a CSV file is uploaded to that endpoint, the backend performs three sequential operations:

1. **CSV Parsing and Data Health Check** (`app/services/csv_parser.py`)
   - Reads the uploaded CSV and maps column aliases (Indonesian or English headers are both accepted)
   - Detects missing values, bad date formats, non-numeric prices, duplicate rows, and statistical outliers
   - Calculates a deterministic `reliability_score` from 0 to 100 with a transparent breakdown (base 100 minus penalties for format issues, duplicates, and outliers)
   - Returns a `data_health` object with the score, a human-readable `warning_message`, color indicator, and a list of `issues` per row and column

2. **Correlation Engine** (`app/services/correlation_engine.py`)
   - Compares product keywords from the uploaded CSV against the static market snapshot in the database (`competitor_prices` table, seeded from `backend/app/scripts/output/competitor_prices.csv`)
   - Calculates `keyword_overlap_score` (how many uploaded product names overlap with known market products)
   - Returns `market_trend_growth` and `trend_reference_source`

3. **LLM Blueprint Generation** (`app/services/llm_service.py`)
   - Builds a structured prompt from the cleaned sales data and correlation metrics
   - Sends the prompt to the locally-running Ollama instance using the `sioslo-model` (a fine-tuned Llama 3 8B GGUF)
   - Parses the response into `InnovationBlueprintItem` objects, each containing:
     - `title` - product innovation title
     - `target_location` - the location the user specified
     - `recommended_price` - suggested selling price in Rupiah
     - `competitor_price_ceiling` - maximum competitor price from seed data
     - `justification` - why this product idea fits the data
     - `risk_factors` - array of business risks to consider
     - `whatsapp_copy_text` - a pre-written promotional message ready to copy and paste

All three results are returned as a single JSON response. No data is stored permanently after the analysis (the frontend stores the result in `sessionStorage` and `localStorage` locally in the browser).

### Frontend (`/frontend`)

A React 19 application built with Vite, TypeScript, and Wouter (client-side routing). It consists of five pages:

- **Landing (`/`)** - Marketing landing page with feature overview and call-to-action
- **Dashboard (`/dashboard`)** - Summary of past analyses stored in browser `localStorage`, stat cards, and quick actions
- **Upload (`/upload`)** - Drag-and-drop CSV upload form with target location input; triggers `POST /api/v1/analyze/` and routes to the Health page on success
- **Data Health (`/health`)** - Displays the `data_health` object from the API: reliability score gauge, issue breakdown by type, CSV column status list, score breakdown formula, and AI transparency metrics from `correlation_metrics`
- **Innovation Lab (`/lab`)** - Displays `innovation_blueprint` cards with price comparison, justification, risk factors accordion, and the WhatsApp copy button

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend API | FastAPI | Latest |
| Database | PostgreSQL | 16 |
| AI Runtime | Ollama | Latest |
| AI Model | Fine-tuned Llama 3 (GGUF) | sioslo-model |
| ORM | SQLAlchemy + Alembic | Latest |
| Frontend Framework | React | 19 |
| Frontend Build Tool | Vite | 7 |
| Frontend Router | Wouter | Latest |
| Package Manager (Frontend) | pnpm | 8+ |
| Container | Docker + Docker Compose | Latest |

---

## Prerequisites

Install the following tools before starting. All are required.

### 1. Git

Used to clone the repository from GitHub.

Download: https://git-scm.com/downloads

Verify installation:
```
git --version
```

### 2. Docker Desktop

Used to run PostgreSQL, Ollama, and the FastAPI backend as containers.

Download: https://www.docker.com/products/docker-desktop/

IMPORTANT: After installing Docker Desktop, open the application and wait until the Docker icon in your system tray shows it is running. Docker must be running in the background before you execute any `docker compose` commands.

Verify installation:
```
docker --version
docker compose version
```

### 3. Node.js (LTS)

Used to run the frontend development server.

Download: https://nodejs.org/ - select the LTS (Long Term Support) version.

Verify installation:
```
node --version
```

### 4. pnpm

The frontend uses pnpm as its package manager, not npm or yarn.

Install via corepack (recommended, included with Node.js):
```
corepack enable
```

Or install globally via npm:
```
npm install -g pnpm
```

Verify installation:
```
pnpm --version
```

### 5. SiOslo AI Model File

The fine-tuned Llama 3 model weights are too large for GitHub and must be downloaded separately.

Download link: https://drive.google.com/file/d/1k6AcIdwpwQAG_HiNC5C_SDBiw2YpCqZK/view?usp=drive_link

The file is named `sioslo-llama3.gguf`. Save it somewhere accessible - you will move it into the project folder in Step 3.1 below.

---

## Full Setup Guide

Follow every step in order. Do not skip any step.

### Step 1 - Clone the Repository

Open PowerShell (Windows) or Terminal (Mac/Linux) and run:

```
git clone https://github.com/danishshxx/SiOslo.git
cd SiOslo
```

After this command completes, you will have a folder named `SiOslo` containing two sub-folders: `backend` and `frontend`.

---

### Step 2 - Create the Backend Environment Configuration File

The backend requires a `.env` file to connect to the database and the AI model. This file is not included in the repository for security reasons.

Navigate into the backend folder:

```
cd backend
```

Create a new file named exactly `.env` (note: the filename starts with a dot and has no extension). In Notepad on Windows, save the file as "All Files" type and name it `.env`.

Copy and paste the following content exactly into the file:

```
APP_NAME="SiOslo: Market-Driven R&D Buddy"
APP_ENV="docker"
DEBUG=True

DATABASE_URL=postgresql://user:kembalikesolomantaphuehue@db:5432/smart_commerce

LLM_ENDPOINT=http://ollama:11434/api/generate
LLM_MODEL_NAME=sioslo-model
```

Save and close the file.

IMPORTANT NOTES about this configuration:
- `db` and `ollama` are Docker service names, not `localhost`. Inside Docker, containers talk to each other by service name. If you use `localhost` here, the API container will fail to connect.
- The password `kembalikesolomantaphuehue` must match exactly. If it does not match, the database will reject the connection. If you ever need to change it, you must first destroy the existing database volume with `docker compose down -v` and rebuild from scratch.
- `LLM_MODEL_NAME=sioslo-model` must match the model name you will register in Step 5.

---

### Step 3 - Place the AI Model File

Move the `sioslo-llama3.gguf` file you downloaded in the Prerequisites section into this exact folder:

```
SiOslo/backend/models/
```

After moving, verify the folder contains these files:

```
SiOslo/backend/models/
    sioslo-llama3.gguf      <- the model weights you just moved here
    Modelfile               <- already exists in the repo
    ollama-entrypoint.sh    <- already exists in the repo
```

IMPORTANT for Windows users: The file `ollama-entrypoint.sh` must use Unix-style LF line endings, not Windows CRLF. If this file was checked out with CRLF endings, the Ollama container will crash with an error like `$'\r': command not found`.

To fix line endings, run this in Git Bash or WSL:
```
sed -i 's/\r//' backend/models/ollama-entrypoint.sh
```

Or configure Git globally to not convert line endings:
```
git config --global core.autocrlf false
```

---

### Step 4 - Start the Backend with Docker

Make sure Docker Desktop is running. Then, from inside the `backend` folder, run:

```
docker compose up -d --build
```

This command does the following:
- Builds Docker images for the API and frontend containers
- Downloads the PostgreSQL 16 and Ollama base images if not already cached (this may take several minutes on first run)
- Starts three containers:
  - `smart_commerce_db` - PostgreSQL database
  - `smart_commerce_llm` - Ollama AI runtime
  - `smart_commerce_api` - FastAPI application (waits for the database to be healthy, then runs Alembic migrations and starts the server)

Wait approximately 30-60 seconds after this command returns. Then verify all three containers are running:

```
docker compose ps
```

You should see all three containers with status `running` or `healthy`.

If the `smart_commerce_api` container shows a status other than running, check its logs:

```
docker compose logs api --tail=50
```

A successful startup log will end with:
```
Application startup complete.
```

You can also verify the API is responding by opening this URL in your browser:
```
http://localhost:8000/docs
```

This will show the FastAPI interactive documentation (Swagger UI).

---

### Step 5 - Import Market Seed Data

The database starts empty. The correlation engine needs competitor price data to function. This data is already included in the repository at `backend/app/scripts/output/`.

Run these two commands from inside the `backend` folder:

Command 1 - Copy the CSV files into the running API container:
```
docker cp app/scripts/output smart_commerce_api:/app/app/scripts/
```

Command 2 - Run the import script inside the container:
```
docker exec -it smart_commerce_api python -m app.scripts.import_csv
```

You should see output confirming that rows were inserted into the database. The seed data contains 137 rows of competitor prices across categories including Minuman (beverages), Kecantikan (beauty), Aksesori (accessories), and others.

---

### Step 6 - Build and Register the AI Model

The Ollama container is running but it does not yet know about the `sioslo-model`. You must register it by running this command:

```
docker exec smart_commerce_llm ollama create sioslo-model -f /models/ModelFile
```

This command reads the `Modelfile` (which references `sioslo-llama3.gguf`) and registers it as a named model called `sioslo-model` inside the Ollama container.

This command may take 1-3 minutes to complete on first run.

After it finishes, warm up the model so it is loaded into memory and will not time out on the first real request:

```
docker exec -it smart_commerce_api python -c "import httpx; r=httpx.post('http://ollama:11434/api/generate', json={'model':'sioslo-model','prompt':'tes','stream':False}, timeout=300.0); print('Warmup status:', r.status_code)"
```

Expected output:
```
Warmup status: 200
```

If you see `Warmup status: 200`, the entire backend stack is fully operational.

---

### Step 7 - Start the Frontend

Open a new terminal window. Navigate to the `frontend` folder inside your cloned project:

```
cd SiOslo/frontend
```

Install all Node.js dependencies:

```
pnpm install
```

Start the development server:

```
pnpm dev
```

Wait for the terminal to show output similar to:
```
VITE v7.x.x  ready in xxx ms
  Local:   http://localhost:3000/
```

The frontend is now running.

---

### Step 8 - Open the Application

Open your web browser and navigate to:
```
http://localhost:3000
```

For the best experience, use an Incognito or Private Window to avoid browser cache issues from previous sessions.

---

## Using the Application

### Full Analysis Flow

1. From the landing page, click **Analyze Your Data** or navigate to **http://localhost:3000/upload**
2. On the Upload page, enter a target market location in the text field (example: `Jakarta`, `Surabaya`, `Bandung`)
3. Either drag and drop a CSV file onto the upload area, or click the area to open a file picker
4. Click **Analyze Data**
5. The page will show a loading state with step-by-step progress messages as the CSV is validated, correlated, and sent to the local AI model
6. When the analysis completes, the browser automatically navigates to the **Data Health** page (`/health`)
7. After reviewing the data health report, click **Continue to Innovation Blueprint** to see the AI-generated product recommendations on the **Innovation Lab** page (`/lab`)
8. On each blueprint card, click **Copy for WhatsApp** to copy the pre-written promotional message to your clipboard

### Required CSV Columns

Your CSV file must contain these six columns. The system accepts both English and Indonesian column names:

| Required Column | Accepted Indonesian Aliases |
|----------------|---------------------------|
| `transaction_date` | `tanggal`, `date`, `tgl` |
| `product_name` | `nama produk`, `produk`, `nama_produk` |
| `category` | `kategori` |
| `qty_sold` | `terjual`, `qty sold`, `jumlah terjual` |
| `remaining_stock` | `sisa stok`, `stok sisa`, `remaining stock` |
| `unit_price` | `harga satuan`, `harga`, `price` |

Additional columns in your CSV are ignored. The system only reads the six required columns.

### CSV Date Format

Dates in the `transaction_date` column should follow one of these formats:
- `YYYY-MM-DD` (example: `2026-03-15`)
- `DD/MM/YYYY` (example: `15/03/2026`)
- `DD-MM-YYYY` (example: `15-03-2026`)

### Understanding the Data Health Score

The reliability score is calculated deterministically using this formula:

```
score = 100
score -= (number of format issues / total rows) * 30
score -= (number of duplicate rows / total rows) * 20
score -= (number of statistical outliers / total rows) * 10
score = max(0, min(100, score))
```

A score of 80 or above is considered healthy. Between 60 and 79 the AI can still proceed but with lower confidence. Below 60, the recommendations may be unreliable.

---

## Port Reference

| Service | Host Port | Internal Port | URL |
|---------|-----------|---------------|-----|
| Frontend (Vite dev server) | 3000 | 3000 | http://localhost:3000 |
| Backend (FastAPI) | 8000 | 8000 | http://localhost:8000 |
| API Documentation | 8000 | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | 5432 | postgresql://localhost:5432/smart_commerce |
| Ollama | 11434 | 11434 | http://localhost:11434/api/tags |

---

## Stopping the Application

Stop the frontend (in the terminal running `pnpm dev`):
```
Ctrl + C
```

Stop the backend containers:
```
cd backend
docker compose stop
```

To stop and remove containers but keep the database data:
```
docker compose down
```

To stop, remove containers, and delete all database data (full reset):
```
docker compose down -v
```

---

## Troubleshooting

### The browser shows a blank screen or "apiConfigurationNotice is not a function"

The file `frontend/client/src/lib/sioslo-api.ts` is missing or empty. This file is tracked in git but may be affected by line ending conversion. Check if it exists and contains the `analyzeCsv` export function. If it is empty or missing, restore it from git:

```
git checkout frontend/client/src/lib/sioslo-api.ts
```

### The page shows "Failed to fetch" or "Network Error" when clicking Analyze Data

This means the frontend cannot reach the backend API. Check:
1. Is the `smart_commerce_api` container running? Run `docker compose ps` from the backend folder.
2. Is the API responding? Open `http://localhost:8000/docs` in your browser.
3. Has CORS been configured? The `CORSMiddleware` in `backend/app/main.py` must allow `http://localhost:3000`.

### The analysis completes but Innovation Blueprint shows no cards

This means the LLM returned an empty or unparseable response. Check:
1. Has the model been warmed up? Run the warmup command from Step 6.
2. Are the Ollama logs clean? Run `docker compose logs llm --tail=30`.
3. Is `LLM_MODEL_NAME=sioslo-model` in your `.env` file?

### Docker reports "password authentication failed for user"

Your `.env` file has a different password from what the database container was initialized with. The database initializes with the password from the first time it starts. If you change the password later, the old data remains with the old password.

Fix: destroy the database volume and restart from scratch:
```
docker compose down -v
docker compose up -d --build
```
Then repeat Steps 5 and 6.

### Port 3000 is already in use when running docker compose up

Docker is trying to start a frontend container that uses port 3000, but `pnpm dev` is already using that port locally. Either stop `pnpm dev` before running `docker compose up`, or run only the backend services:
```
docker compose up -d db llm api
```

### The Ollama container crashes with "$'\r': command not found"

The `ollama-entrypoint.sh` file has Windows CRLF line endings. Fix it using Git Bash or WSL:
```
sed -i 's/\r//' backend/models/ollama-entrypoint.sh
```
Then restart the container:
```
docker compose restart llm
```

### TypeScript error "Cannot find module @/lib/utils"

This file was recently added to the repository. Pull the latest changes:
```
git pull origin main
```
Then verify `frontend/client/src/lib/utils.ts` exists. If not, create it with this content:
```typescript
import { clsx, type ClassValue } from "clsx";
export function cn(...inputs: ClassValue[]) { return clsx(inputs); }
```

### The tsconfig.json shows "Invalid value for --ignoreDeprecations"

Pull the latest changes from the repository:
```
git pull origin main
```
This issue was fixed in commit `6e061a0`. The `"ignoreDeprecations": "6.0"` line has been removed from `tsconfig.json`.

---

## Repository Structure

```
SiOslo/
    backend/
        app/
            api/v1/endpoints/
                analyze.py          <- primary endpoint POST /api/v1/analyze/
                chat.py             <- AI chat endpoint (UI only, no frontend integration yet)
                simulate.py         <- simulation endpoint (UI only, no frontend integration yet)
                sales.py            <- legacy CSV upload endpoint
                market.py           <- market data endpoint
                insight.py          <- insight endpoint
            core/
                config.py           <- reads .env settings
                database.py         <- SQLAlchemy session setup
            models/                 <- SQLAlchemy table definitions
            schemas/
                analysis.py         <- Pydantic response schemas (source of truth for API shape)
            scripts/
                import_csv.py       <- seeds competitor_prices from CSV into the database
                output/
                    competitor_prices.csv   <- 137 rows of seed market data
                    demographics.csv        <- demographic reference data
            services/
                csv_parser.py       <- data health check and CSV normalization
                correlation_engine.py   <- keyword overlap and market trend correlation
                llm_service.py      <- Ollama prompt builder and blueprint parser
        models/
            sioslo-llama3.gguf      <- NOT in git; must be downloaded separately
            Modelfile               <- Ollama model registration file
            ollama-entrypoint.sh    <- Docker entrypoint for Ollama container
        alembic/                    <- database migration scripts
        docker-compose.yml          <- defines db, llm, and api services
        Dockerfile                  <- FastAPI container image definition
        .env                        <- NOT in git; must be created manually (see Step 2)
    frontend/
        client/src/
            App.tsx                 <- single-file React app with all 5 pages
            index.css               <- custom CSS design system (no Tailwind)
            lib/
                sioslo-api.ts       <- TypeScript interfaces and analyzeCsv() fetch function
                utils.ts            <- cn() class utility for shadcn UI components
        Dockerfile                  <- frontend container image definition
        vite.config.ts              <- Vite configuration
        package.json                <- frontend dependencies
    README.md                       <- this file
```

---

## API Reference

### POST /api/v1/analyze/

The only endpoint used by the frontend.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | A CSV file containing sales data |
| `target_lokasi` | string | Target market location (example: "Jakarta") |

**Response:** `application/json`

```json
{
  "status": "success",
  "data_health": {
    "reliability_score": 100,
    "status_color": "green",
    "warning_message": "Data penjualan sehat dan konsisten. Analisis dapat dilanjutkan.",
    "score_breakdown": {
      "base_score": 100,
      "format_issue_penalty": 0,
      "duplicate_penalty": 0,
      "outlier_penalty": 0,
      "final_score": 100
    },
    "issues": []
  },
  "correlation_metrics": {
    "keyword_overlap_score": 0.0278,
    "market_trend_growth": "+0%",
    "trend_reference_source": "static_snapshot"
  },
  "innovation_blueprint": [
    {
      "id": "inv-001",
      "title": "Inovasi Payung Lipat Polos Dewasa untuk Jakarta",
      "target_location": "Jakarta",
      "recommended_price": 40500,
      "competitor_price_ceiling": 172242,
      "justification": "Dead-stock resurrection opportunity based on sales pattern analysis.",
      "risk_factors": ["Market response needs testing", "Raw material availability"],
      "whatsapp_copy_text": "Coba produk spesial kami untuk Jakarta! Lebih terjangkau, lebih cocok buat kamu."
    }
  ]
}
```

---

## License and Copyright

Copyright 2026 Kembali Ke Solo Team

- Muhammad Danish Abrisam
- Hudzaifah
- Farras Dary Santosa
- Andi Rifanti Fitrah Riwan Lewa
- Vallencia Febriana

This project was built for Compfest UI 2026 - AIC (AI Innovation Challenge). All rights reserved.
