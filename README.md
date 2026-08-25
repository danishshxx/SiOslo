# 🚀 SiOslo: Market-Driven R&D Buddy

SiOslo is an AI-powered product intelligence platform designed specifically for product-based SMBs (UMKM). It analyzes historical sales data and external market trends to generate actionable product innovation blueprints. 

Built with a strict **Local & Private-First** philosophy, all data processing and LLM inferences run 100% locally on your machine. Financial data never leaves the device.

---

## 🛠️ Tech Stack & Architecture

SiOslo is built as a containerized full-stack application:
*   **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, shadcn-ui.
*   **Backend:** FastAPI (Python), PostgreSQL, SQLAlchemy.
*   **AI Engine:** Local LLM via Ollama (Llama-3 8B fine-tuned/prompt-engineered).
*   **Infrastructure:** Fully dockerized (Frontend, API, Database, and LLM containers).

---

## ⚙️ Prerequisites

To run this project, you only need one thing installed on your machine:
*   **Docker Desktop** (Make sure the Docker daemon is running).
*   *No need to manually install Node.js, Python, PostgreSQL, or Ollama.*

---

## 🚀 How to Run Locally

We have configured a unified `docker-compose.yml` to orchestrate the entire stack.

**1. Clone the repository**
\`\`\`bash
git clone https://github.com/danishshxx/SiOslo.git
cd SiOslo
\`\`\`

**2. Navigate to the backend directory (where the orchestration file is located)**
\`\`\`bash
cd backend
\`\`\`

**3. Build and spin up the containers**
\`\`\`bash
docker-compose up --build -d
\`\`\`
*(Note: The initial build might take a few minutes as it downloads the base images for Python, Node.js, PostgreSQL, and Ollama).*

**4. Access the Application**
Once the containers are successfully running, you can access:
*   **Web Application (Frontend):** [http://localhost:3000](http://localhost:3000)
*   **Backend API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Demo / Testing Guide for Judges

To experience the full flow of the SiOslo MVP, follow these steps:

1.  **Open the Web App:** Go to `http://localhost:3000`. You will see the cinematic landing page. Click **"Get Started"** or **"Analyze Your Data"**.
2.  **Upload Data:** 
    *   On the Upload page, type a Target Location (e.g., `Jakarta`).
    *   Drag and drop a sample CSV file. *(You can use `test.csv` provided in the `backend/tests/` folder).*
3.  **Run Analysis:** Click the **"Analyze Data"** button. 
    *   *Notice the dynamic loading states—the backend is currently parsing the CSV, running a deterministic correlation engine against synthetic market data, and prompting the local Llama-3 model to generate product ideas.*
4.  **Review Data Health:** You will be redirected to the **Data Health Dashboard**. This shows the deterministic evaluation of your CSV quality (missing values, duplicates, outliers) before it is fed to the LLM.
5.  **View Innovation Blueprint:** Click **"Continue to Innovation Blueprint"** to see the AI-generated product recommendations, complete with pricing strategies and risk mitigation.
6.  **Explore the UI:** Click on the **Simulation** and **AI Buddy** tabs in the navigation bar to see our planned features for the production release.

---

## 🛑 Important Notes for MVP
*   **LLM Cold Start:** The very first time you run the analysis, Ollama might take some time to load the model into memory. Subsequent runs will be significantly faster.
*   **Mocked Services:** For this hackathon MVP, the "Simulation" and "AI Buddy" features are frontend showcases (UI/UX only) and are marked as "Coming Soon" in the navigation. The core logic resides heavily in the Data Health and Innovation Blueprint generation.
*   **Market Data:** The external market trends are currently sourced from a static synthetic dataset imported during the database initialization phase to ensure deterministic output during the judging process.

---

## 📝 License
MIT License. Copyright (c) 2026 Muhammad Danish Abrisam.