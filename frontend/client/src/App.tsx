/* SiOslo frontend — single-file React app using wouter routing and custom CSS design system. */
import { useRef, useState, useEffect } from "react";
import { Link, Route, Switch, useLocation } from "wouter";
import {
  ArrowRight, BarChart3, CheckCircle2, ChevronRight, ChevronDown,
  Database, FileText, Lightbulb, LineChart, Menu,
  MessageCircle, Shield, Sparkles, Upload, User, X, Zap, AlertTriangle,
  TrendingUp, Clock, Copy
} from "lucide-react";
import { Toaster, toast } from "sonner";
import {
  analyzeCsv, apiConfigurationNotice,
  type AnalysisResponse, type InnovationBlueprintItem
} from "./lib/sioslo-api";


/* Local storage helpers for analysis history and current session. */

type HistoryItem = {
  id: string; filename: string; date: string; rows?: number;
  score: number; status: string; analysis: AnalysisResponse;
};
function loadHistory(): HistoryItem[] {
  try { return JSON.parse(localStorage.getItem("sioslo-analysis-history") || "[]") as HistoryItem[]; }
  catch { return []; }
}
function persistHistory(items: HistoryItem[]) {
  localStorage.setItem("sioslo-analysis-history", JSON.stringify(items.slice(0, 24)));
}
function saveCurrentAnalysis(item: HistoryItem) {
  sessionStorage.setItem("sioslo-current-analysis", JSON.stringify(item));
}
function loadCurrentAnalysis(): HistoryItem | null {
  try { const raw = sessionStorage.getItem("sioslo-current-analysis"); return raw ? JSON.parse(raw) as HistoryItem : null; }
  catch { return null; }
}

/* Shared brand wordmark component. */

function Logo() {
  return <span className="sioslo-logo logo">SiOSLO</span>;
}

/* ═══════════════════════════════════════════════
   LANDING NAV (Dynamic Centered Logo & Vertical Dock)
═══════════════════════════════════════════════ */
function LandingNav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <>
      {/* 🌟 NAVBAR HORIZONTAL UTAMA (Tetap ada, kontennya dinamis) 🌟 */}
      <div className={`landing-nav-dynamic ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="nav-container">
          
          {/* Logo (Geser dari Kiri ke Tengah secara mulus) */}
          <div className="nav-logo-wrapper">
            <a href="#top"><Logo /></a>
          </div>
          
          {/* Menu Tengah (Menghilang saat di-scroll) */}
          <ul className="nav-center-links dash-nav-pills hidden md:flex" style={{ margin: 0, padding: 0 }}>
            <li><a href="#product" className="dash-nav-pill"><BarChart3 size={14} />Product</a></li>
            <li><a href="#solutions" className="dash-nav-pill"><Sparkles size={14} />Solutions</a></li>
            <li><a href="#how" className="dash-nav-pill"><LineChart size={14} />How It Works</a></li>
          </ul>
          
          {/* Tombol Kanan (Menghilang saat di-scroll) */}
          <div className="nav-right-actions hidden md:flex">
            <Link href="/dashboard" className="nav-signin" style={{ padding: '8px 12px' }}>Sign In</Link>
            <Link href="/dashboard" className="nav-get-started">Get Started <ArrowRight size={14} /></Link>
          </div>
          
          {/* Hamburger Menu Mobile */}
          <button className="nav-hamburger md:hidden flex" onClick={() => setOpen(!open)} aria-label="Menu" style={{ position: 'absolute', right: '20px' }}>
            {open ? <X size={20} color="#fff" /> : <Menu size={20} color="#fff" />}
          </button>
        </div>
      </div>

      {/* 🌟 MENU VERTIKAL KIRI (Muncul saat di-scroll) 🌟 */}
      <div className={`scrolled-left-dock group hidden md:flex ${scrolled ? 'is-visible' : ''}`}>
        <ul className="dock-links">
          <li><a href="#product" className="dock-link"><BarChart3/><span className="dock-label">Product</span></a></li>
          <li><a href="#solutions" className="dock-link"><Sparkles/><span className="dock-label">Solutions</span></a></li>
          <li><a href="#how" className="dock-link"><LineChart/><span className="dock-label">How It Works</span></a></li>
        </ul>
        
        <div className="dock-divider"></div>
        
        <Link href="/dashboard" className="dock-cta">
          <div className="dock-cta-icon"><ArrowRight size={16} /></div>
          <span className="dock-label">Get Started</span>
        </Link>
      </div>

      {/* Laci Menu Mobile (Tetap sama) */}
      {open && (
        <div className="dash-mobile-drawer fixed top-20 left-4 right-4 z-[100]" style={{ 
          display: 'flex', 
          background: 'rgba(10, 15, 30, 0.95)', 
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '16px'
        }}>
          <a href="#product" className="dash-nav-pill" onClick={() => setOpen(false)}>Product</a>
          <a href="#solutions" className="dash-nav-pill" onClick={() => setOpen(false)}>Solutions</a>
          <a href="#how" className="dash-nav-pill" onClick={() => setOpen(false)}>How It Works</a>
          <Link href="/dashboard" onClick={() => setOpen(false)} className="nav-get-started" style={{ textAlign: "center", marginTop: '12px', justifyContent: 'center' }}>
            Get Started
          </Link>
        </div>
      )}
    </>
  );
}

/* ═══════════════════════════════════════════════
   DASHBOARD NAV
═══════════════════════════════════════════════ */
function DashboardNav() {
  const [open, setOpen] = useState(false);
  const [location] = useLocation();

  const items = [
    { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { href: "/upload", label: "Upload", icon: Upload },
    { href: "/health", label: "analysis data", icon: LineChart },
    { href: "/lab", label: "Innovation lab", icon: Sparkles },
    { href: "/simulation", label: "Simulation", icon: Zap },
    { href: "/buddy", label: "AI Buddy", icon: MessageCircle },
  ];

  const isActive = (href: string, label: string) => {
    if (href === location) return true;
    if (label === "analysis data" && location === "/health") return true;
    if (label === "Innovation lab" && location === "/lab") return true;
    if (label === "Upload" && location === "/upload") return true;
    return false;
  };

  return (
    <div className="dash-topnav-outer">
      <div className="dash-topnav">
        <Link href="/"><Logo /></Link>
        <nav className="dash-nav-pills">
          {items.map(({ href, label, icon: Icon }) => (
            <Link
              key={label}
              href={href}
              className={`dash-nav-pill ${isActive(href, label) ? "active" : ""}`}
            >
              <Icon size={15} />{label}
            </Link>
          ))}
        </nav>
        <div className="dash-nav-right">
          <button className="dash-avatar" aria-label="Profile">
            <User size={16} />
          </button>
        </div>
        <button className="nav-hamburger" onClick={() => setOpen(!open)} aria-label="Menu">
          <Menu size={20} />
        </button>
      </div>
      {open && (
        <div className="dash-mobile-drawer">
          {items.map(({ href, label }) => (
            <Link 
              key={label} 
              href={href} 
              className="dash-nav-pill" 
              onClick={() => setOpen(false)}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Dashboard shell (Added Fade Transition) ─── */
function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="dashboard-shell">
      <DashboardNav />
      {/* Magic trick 1: Smooth page transitions */}
      <main className="dashboard-content animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out">
        <div className="dash-wrap">{children}</div>
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   LANDING PAGE  
═══════════════════════════════════════════════ */
function Landing() {
  return (
    <div className="landing-page" id="top">
      <div className="landing-bg-art" />
      <LandingNav />

      <main>
        {/* ── Hero ── */}
        <section className="l-hero">
          <div className="l-hero-inner">
            <div className="l-eyebrow-pill">AI-Powered Analytics for SMBs</div>
            <h1 className="l-hero-wordmark">SiOSLO</h1>
            <h2 className="l-hero-headline">AI-Powered Analytics for<br />SMBs</h2>
            <p className="l-hero-sub">Turn Your Sales Data Into Smarter Product Decisions</p>

            <div className="l-hero-ctas">
              <Link href="/upload" className="l-cta-outline">
                Analyze Your Data
              </Link>
              <a href="#how" className="l-cta-ghost">
                How It Works
              </a>
            </div>

            <div className="l-scroll-cue">
              <div className="l-mouse">
                <div className="l-mouse-dot" />
              </div>
            </div>
          </div>
        </section>

        {/* ── Our Product ── */}
        <section className="l-product" id="product">
          <div className="l-section-inner">
            <div className="l-product-eyebrow">
              <span className="l-plus-dot">+</span> OUR PRODUCT
            </div>
            <h2 className="l-product-headline">
              Everything You Need to<br />Make{" "}
              <span className="l-gradient-text">Better Product Decisions</span>
            </h2>
            <p className="l-product-sub">
              Market-Driven R&D Buddy combines AI-powered analysis with market intelligence
              to help SMBs discover opportunities and reduce R&D guesswork.
            </p>

            <div className="l-feature-grid">
              {[
                { icon: <BarChart3 />, color: "blue", title: "AI Data Analysis", sub: "Understand your data deeply", body: "Upload your sales CSV and our AI instantly discovers top products, slow movers, stock issues, and patterns." },
                { icon: <Sparkles />, color: "purple", title: "Innovation Lab", sub: "Generate winning ideas", body: "Turn data and market trends into actionable product ideas, bundling opportunities, and market gaps." },
                { icon: <LineChart />, color: "teal", title: "Simulation", sub: "Test before you decide", body: "Run what-if scenarios for pricing, production, and bundles to predict outcomes and reduce business risk." },
                { icon: <Sparkles />, color: "orange", title: "AI Buddy", sub: "Your data, answered", body: "Ask anything about your data, strategies, or product ideas. Get instant, contextual answers." },
                { icon: <Shield />, color: "blue", title: "Privacy & Local Processing", sub: "Secure. Local. Yours.", body: "100% local processing ensures your financial and sales data never leaves your device. No cloud." },
                { icon: <TrendingUp />, color: "purple", title: "Data Health Dashboard", sub: "Accuracy before insight", body: "SiOSLO checks encoding, missing values, duplicates, and business outliers before the model responds." },
              ].map(({ icon, color, title, sub, body }) => (
                <div className="l-feature-card" key={title}>
                  <div className={`l-f-icon l-f-icon--${color}`}>{icon}</div>
                  <h3>{title}</h3>
                  <p className="l-f-sub">{sub}</p>
                  <p className="l-f-body">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Solutions ── */}
        <section className="l-solutions" id="solutions">
          <div className="l-section-inner">
            <div className="l-section-label">✦ Solutions</div>
            <h2 className="l-section-h2 l-grad">Make better product decisions</h2>
            <p className="l-section-p">We help product-based SMBs turn their sales data and market trends into actionable product opportunities.</p>
            <div className="l-steps">
              {[["01", "Understand", "See what your sales data is telling you."], ["02", "Discover", "Find market trends and opportunities that matter."], ["03", "Decide", "Get clear AI recommendations on what to produce next."]].map(([num, title, body]) => (
                <div className="l-step-card" key={num}>
                  <div className="l-step-num">{num}</div>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section className="l-how" id="how">
          <div className="l-section-inner">
            <div className="l-section-label">✦ How It Works</div>
            <h2 className="l-section-h2">From your data to your next product</h2>
            <p className="l-section-p">SiOSLO connects your business signals with market context to guide the next decision.</p>
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="l-footer">
          <Logo />
          <p>© 2026 SiOSLO. AI-Powered Analytics for SMBs.</p>
          <div className="l-footer-links">
            <a href="#product">Product</a>
            <a href="#solutions">Solutions</a>
            <a href="#how">How It Works</a>
          </div>
        </footer>
      </main>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   DASHBOARD  
═══════════════════════════════════════════════ */
function StatCard({ icon, label, value, foot }: { icon: React.ReactNode; label: string; value: string; foot: string }) {
  return (
    <div className="db-stat-card">
      <div className="db-stat-icon">{icon}</div>
      <p className="db-stat-label">{label}</p>
      <p className="db-stat-value">{value}</p>
      <p className="db-stat-foot">{foot}</p>
    </div>
  );
}

function ReportRows({ history, onOpen }: { history: HistoryItem[]; onOpen: (item: HistoryItem) => void }) {
  return (
    <section className="db-reports">
      <div className="db-section-head">
        <h2>Recent Reports</h2>
        <Link href="/upload" className="db-new-upload">+ New Upload</Link>
      </div>
      {history.length === 0 ? (
        <div className="db-report-row">
          <div className="db-report-left">
            <div className="db-report-icon"><FileText size={17} /></div>
            <div>
              <p className="db-report-title">No saved reports yet</p>
              <p className="db-report-meta">Upload a CSV to create your first analysis.</p>
            </div>
          </div>
        </div>
      ) : (
        history.slice(0, 4).map((item) => (
          <button className="db-report-row db-report-btn" key={item.id} onClick={() => onOpen(item)}>
            <div className="db-report-left">
              <div className="db-report-icon"><FileText size={17} /></div>
              <div>
                <p className="db-report-title">{item.filename.replace(".csv", "").replace(/_/g, " ")}</p>
                <p className="db-report-meta">
                  {new Date(item.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                  {item.rows ? ` · ${item.rows} rows` : ""}
                </p>
              </div>
            </div>
            <div className="db-report-right">
              <span className="db-score-chip">Score {item.score}</span>
              <span className="db-ideas-chip">
                {item.analysis.innovation_blueprint?.length || 0} innovation ideas
              </span>
              <span className="db-complete-chip"><CheckCircle2 size={13} /> Complete</span>
              <ChevronRight size={14} className="db-chevron" />
            </div>
          </button>
        ))
      )}
    </section>
  );
}

function Dashboard() {
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory);
  const [, setLocation] = useLocation();

  const totalRows = history.reduce((n, h) => n + (h.rows || 0), 0);
  const totalIdeas = history.reduce((n, h) => n + (h.analysis.innovation_blueprint?.length || 0), 0);

  return (
    <Shell>
      {/* Welcome header */}
      <div className="db-page-head">
        <div>
          <h1>Welcome!</h1>
          <p className="db-page-sub">Here is a summary of your data analysis activity.</p>
        </div>
        <div className="db-head-actions">
          <Link href="/upload" className="db-btn-primary"><Upload size={15} /> Upload Data</Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="db-stats-grid">
        <StatCard icon={<LineChart size={17} />} label="Analyses This Month" value={`${Math.min(history.length, 3)}/3`} foot="slots used" />
        <StatCard icon={<Database size={17} />} label="Total Rows Analyzed" value={totalRows > 0 ? String(totalRows) : "0"} foot="data rows processed" />
        <StatCard icon={<FileText size={17} />} label="Saved Reports" value={String(history.length)} foot="reports ready to view" />
        <StatCard icon={<Lightbulb size={17} />} label="Innovation Ideas Generated" value={String(totalIdeas)} foot="ideas ready to execute" />
      </div>

      {/* Privacy banner */}
      <div className="db-privacy-banner">
        <span className="db-privacy-dot" />
        <p><span>100% Local &amp; Offline —</span> Your financial data never leaves this device. No cloud, no third-party servers.</p>
      </div>

      {/* Reports */}
      <ReportRows
        history={history}
        onOpen={(item) => { saveCurrentAnalysis(item); setLocation("/health"); }}
      />

      {/* Quick actions */}
      <div className="db-quick-grid">
        <Link href="/upload" className="db-quick-card">
          <div className="db-quick-icon"><Upload size={18} /></div>
          <div>
            <p className="db-quick-title">Upload New Data</p>
            <p className="db-quick-sub">Start a fresh analysis with a new CSV</p>
          </div>
        </Link>
        <Link href="/lab" className="db-quick-card">
          <div className="db-quick-icon"><Sparkles size={18} /></div>
          <div>
            <p className="db-quick-title">View Innovation Lab</p>
            <p className="db-quick-sub">{totalIdeas > 0 ? `${totalIdeas} innovation ideas ready to execute` : "Run an analysis to generate ideas"}</p>
          </div>
        </Link>
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   UPLOAD CSV PAGE (Updated with dynamic LLM loading)
═══════════════════════════════════════════════ */
function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState("Jakarta");
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [btnSliding, setBtnSliding] = useState(false);
  const [loadingText, setLoadingText] = useState("Analyzing..."); // Magic trick 2
  const [history, setHistory] = useState<HistoryItem[]>(loadHistory);
  const [, setLocation] = useLocation();
  const inputRef = useRef<HTMLInputElement>(null);
  const notice = apiConfigurationNotice();

  const choose = (next?: File | null) => {
    if (!next) return;
    if (!next.name.toLowerCase().endsWith(".csv")) return toast.error("Only .csv files are accepted");
    setFile(next);
  };

  const run = async () => {
    if (!file) return toast.error("Select a CSV file first");
    
    await new Promise(r => setTimeout(r, 600));
    setLoading(true);

    setLoadingText("Validating CSV structure...");
    setTimeout(() => setLoadingText("Correlating with market trends..."), 1500);
    setTimeout(() => setLoadingText("Running local LLM (sioslo-model)..."), 3500);
    setTimeout(() => setLoadingText("Generating Innovation Blueprint..."), 7500);

    try {
      const analysis = await analyzeCsv(file, target);
      const item: HistoryItem = {
        id: crypto.randomUUID(),
        filename: file.name,
        date: new Date().toISOString(),
        rows: 342, // placeholder; real API would return this
        score: analysis.data_health.reliability_score,
        status: analysis.status,
        analysis,
      };
      
      // Magic trick 3: Anti-Duplikat CSV di riwayat
      const filteredHistory = history.filter(h => h.filename !== file.name);
      const next = [item, ...filteredHistory];
      
      setHistory(next);
      persistHistory(next);
      saveCurrentAnalysis(item);
      toast.success("Analysis complete");
      setLocation("/health");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Analysis failed");
      // Hapus setBtnSliding(false) di sini
    } finally {
      setLoading(false);
    }
  };

  const REQUIRED_COLS = ["date", "product_name", "category", "qty_sold", "sell_price", "cogs", "sales_channel", "region", "closing_stock"];

  return (
    <Shell>
      {/* Header */}
      <div className="up-header">
        <h1 className="up-headline">Upload Your Sales Data</h1>
        <h2 className="up-headline-accent">&amp; Get Insights</h2>
        <p className="up-sub">
          Our AI analyzes your historical data + local market trends to generate targeted product innovation recommendations.
        </p>
        <div className="up-privacy-badge">
          <Shield size={18} className="up-shield" />
          <div>
            <p className="up-privacy-title">100% Local &amp; Offline</p>
            <p className="up-privacy-sub">Your financial data never leaves this device — no cloud, no third-party servers.</p>
          </div>
        </div>
      </div>

      {/* Main upload card */}
      <div className="up-card">
        {notice && <div className="up-notice">{notice}</div>}

        <label className="up-target-label">
          Target location
          <input
            className="up-target-input"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="e.g. Jakarta"
          />
        </label>

        {/* Drop zone */}
        <div
          className={`up-dropzone ${drag ? "dragging" : ""} ${file ? "has-file" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); choose(e.dataTransfer.files?.[0]); }}
          onClick={() => !file && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(e) => choose(e.target.files?.[0])}
          />
          {file ? (
            <div className="up-file-selected">
              <CheckCircle2 size={36} className="up-check" />
              <strong>{file.name}</strong>
              <span>Ready to analyze</span>
              <button
                className="up-remove-file"
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="up-dropzone-idle">
              <Upload size={36} className="up-upload-icon" />
              <strong>Drag your CSV file here</strong>
              <span className="up-click-hint">— click to select a file</span>
              <div className="up-only-csv">
                <FileText size={12} /> Only .csv files accepted
              </div>
            </div>
          )}
        </div>

        {/* Required columns */}
        <div className="up-required-cols">
          <p className="up-req-label">REQUIRED COLUMNS</p>
          <div className="up-cols-row">
            {REQUIRED_COLS.map((col) => (
              <span key={col} className="up-col-chip">{col}</span>
            ))}
          </div>
        </div>

        {/* Analyze button with slide animation */}
        {file && (
          <div className="up-analyze-wrap">
            <button
              className={`up-analyze-btn ${btnSliding ? "sliding" : ""}`}
              disabled={loading}
              onClick={run}
            >
              {loading ? (
                <><span className="up-spinner" /> {loadingText}</>
              ) : (
                <><Zap size={16} /> Analyze Data <ArrowRight size={16} className="up-btn-arrow" /></>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Feature pills */}
      <div className="up-features-row">
        <div className="up-feature-pill">
          <Shield size={20} className="up-fp-icon green" />
          <div>
            <p className="up-fp-title">100% Private</p>
            <p className="up-fp-sub">No data leaves your device</p>
          </div>
        </div>
        <div className="up-feature-pill">
          <Clock size={20} className="up-fp-icon blue" />
          <div>
            <p className="up-fp-title">Fast Results</p>
            <p className="up-fp-sub">Analysis in under 60 seconds</p>
          </div>
        </div>
        <div className="up-feature-pill">
          <Sparkles size={20} className="up-fp-icon purple" />
          <div>
            <p className="up-fp-title">AI-Powered</p>
            <p className="up-fp-sub">Llama-3 8B local model</p>
          </div>
        </div>
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   DATA HEALTH DASHBOARD  
═══════════════════════════════════════════════ */
function CircleGauge({ score }: { score: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const isGood = score >= 80;
  const isMid = score >= 60;

  return (
    <div className="dh-gauge-wrap">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="rgba(139,92,246,0.15)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={r} fill="none"
          stroke={isGood ? "#39D5B0" : isMid ? "#A45BFF" : "#FF7089"}
          strokeWidth="12"
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeDashoffset={circ * 0.25}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 1s ease" }}
        />
        <text x="70" y="62" textAnchor="middle" fill="#fff" fontSize="28" fontWeight="700">{score}</text>
        <text x="70" y="80" textAnchor="middle" fill="#8B82A0" fontSize="13">/100</text>
      </svg>
      <div className={`dh-gauge-badge ${isGood ? "good" : isMid ? "mid" : "bad"}`}>
        {isGood ? <><CheckCircle2 size={12} /> Good</> : isMid ? <><AlertTriangle size={12} /> Needs Attention</> : <><AlertTriangle size={12} /> Low Quality</>}
      </div>
    </div>
  );
}

function Health() {
  const item = loadCurrentAnalysis();
  const [, setLocation] = useLocation();

  const health = item?.analysis?.data_health;
  const corr = item?.analysis?.correlation_metrics as any;
  const score = health?.reliability_score ?? 0;
  const issues = health?.issues ?? [];
  const breakdown: any = health?.score_breakdown ?? {};

  const REQUIRED_COLS = [
    "transaction_date", "product_name", "category",
    "qty_sold", "remaining_stock", "unit_price",
  ];

  const issuesByCol: Record<string, number> = {};
  issues.forEach((iss) => {
    if (!iss.column) return;
    issuesByCol[iss.column] = (issuesByCol[iss.column] ?? 0) + 1;
  });

  const allColNames = Array.from(new Set([
    ...REQUIRED_COLS,
    ...Object.keys(issuesByCol),
  ]));

  const colRows = allColNames.map((col) => ({
    name: col,
    ok: !issuesByCol[col],
    issueCount: issuesByCol[col] ?? 0,
  }));

  const okCount = colRows.filter((c) => c.ok).length;
  const missingCount = issues.filter((i) => i.issue_type === "missing_value" || i.issue_type === "bad_numeric" || i.issue_type === "bad_date").length;
  const duplicateCount = issues.filter((i) => i.issue_type === "duplicate").length;
  const outlierCount = issues.filter((i) => i.issue_type === "outlier").length;

  if (!item || !health) {
    return (
      <Shell>
        <div className="lab-empty" style={{ margin: "48px auto", maxWidth: 480 }}>
          <Sparkles size={40} className="lab-empty-icon" />
          <h2>No analysis yet</h2>
          <p>Upload your CSV and run an analysis to see real data health metrics here.</p>
          <Link href="/upload" className="db-btn-primary" style={{ marginTop: 16 }}>
            <Upload size={15} /> Upload CSV to Start
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="dh-header">
        <div>
          <h1 className="dh-title">Data Health Dashboard</h1>
          <p className="dh-sub">
            Quality report for{" "}
            <span className="dh-file-link">{item.filename}</span>
          </p>
        </div>
      </div>

      <div className="dh-score-row">
        <div className="dh-score-card">
          <p className="dh-score-label">RELIABILITY SCORE</p>
          <CircleGauge score={score} />
          <p className="dh-score-caption">{health.warning_message}</p>
        </div>

        <div className="dh-metrics-grid">
          <div className="dh-metric-card">
            <div className="dh-metric-top">
              <AlertTriangle size={18} className="dh-m-icon orange" />
              <span className="dh-m-label">Total Issues</span>
            </div>
            <p className="dh-m-value">{issues.length}</p>
            <p className="dh-m-foot">rows flagged</p>
          </div>
          <div className="dh-metric-card">
            <div className="dh-metric-top">
              <Database size={18} className="dh-m-icon blue" />
              <span className="dh-m-label">Missing / Bad</span>
            </div>
            <p className="dh-m-value">{missingCount}</p>
            <p className="dh-m-foot">format issues</p>
          </div>
          <div className="dh-metric-card">
            <div className="dh-metric-top">
              <FileText size={18} className="dh-m-icon purple" />
              <span className="dh-m-label">Duplicates</span>
            </div>
            <p className="dh-m-value">{duplicateCount}</p>
            <p className="dh-m-foot">rows removed</p>
          </div>
          <div className="dh-metric-card">
            <div className="dh-metric-top">
              <TrendingUp size={18} className="dh-m-icon green" />
              <span className="dh-m-label">Outliers</span>
            </div>
            <p className="dh-m-value">{outlierCount}</p>
            <p className="dh-m-foot">business anomalies</p>
          </div>
        </div>
      </div>

      {breakdown.final_score !== undefined && (
        <div className="dh-section">
          <div className="dh-section-head">
            <h2>Score Breakdown</h2>
            <span className="dh-cols-count">Open formula — base 100 minus penalties</span>
          </div>
          <div className="dh-transparency-grid">
            <div className="dh-trans-card">
              <div className="dh-trans-top"><AlertTriangle size={14} /><span>FORMAT PENALTY</span></div>
              <p className="dh-trans-value">−{breakdown.format_issue_penalty ?? 0}</p>
            </div>
            <div className="dh-trans-card">
              <div className="dh-trans-top"><FileText size={14} /><span>DUPLICATE PENALTY</span></div>
              <p className="dh-trans-value">−{breakdown.duplicate_penalty ?? 0}</p>
            </div>
            <div className="dh-trans-card">
              <div className="dh-trans-top"><TrendingUp size={14} /><span>OUTLIER PENALTY</span></div>
              <p className="dh-trans-value">−{breakdown.outlier_penalty ?? 0}</p>
            </div>
            <div className="dh-trans-card">
              <div className="dh-trans-top"><CheckCircle2 size={14} /><span>FINAL SCORE</span></div>
              <p className="dh-trans-value">{score}/100</p>
            </div>
          </div>
        </div>
      )}

      <div className="dh-section">
        <div className="dh-section-head">
          <h2>CSV Column Status</h2>
          <span className="dh-cols-count">{okCount}/{allColNames.length} columns complete</span>
        </div>
        <div className="dh-col-list">
          {colRows.map(({ name, ok, issueCount }) => (
            <div className="dh-col-row" key={name}>
              <span className={`dh-col-dot ${ok ? "ok" : "warn"}`}>
                {ok ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
              </span>
              <span className={`dh-col-name ${!ok ? "warn-text" : ""}`}>{name}</span>
              <span className={`dh-col-status ${ok ? "complete" : "issue"}`}>
                {ok ? "Complete" : `${issueCount} issue${issueCount > 1 ? "s" : ""}`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {corr && (
        <div className="dh-section">
          <div className="dh-section-head">
            <h2>AI Transparency</h2>
            <span className="dh-black-box-tag">Not a black box</span>
          </div>
          <div className="dh-transparency-grid">
            <div className="dh-trans-card">
              <div className="dh-trans-top"><TrendingUp size={14} /><span>KEYWORD OVERLAP</span></div>
              <p className="dh-trans-value">{Math.round((corr.keyword_overlap_score ?? 0) * 100)}%</p>
            </div>
            <div className="dh-trans-card">
              <div className="dh-trans-top"><Sparkles size={14} /><span>MARKET TREND GROWTH</span></div>
              <p className="dh-trans-value">{corr.market_trend_growth}</p>
            </div>
            {corr.trend_reference_source && (
              <div className="dh-trans-card">
                <div className="dh-trans-top"><Database size={14} /><span>TREND SOURCE</span></div>
                <p className="dh-trans-value">{corr.trend_reference_source}</p>
              </div>
            )}
            <div className="dh-trans-card">
              <div className="dh-trans-top"><Zap size={14} /><span>AI MODEL</span></div>
              <p className="dh-trans-value">sioslo-model (Local)</p>
            </div>
          </div>
        </div>
      )}

      <div className="dh-cta-row">
        <button className="dh-continue-btn" onClick={() => setLocation("/lab")}>
          Continue to Innovation Blueprint <ArrowRight size={16} />
        </button>
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   INNOVATION BLUEPRINT / LAB  
═══════════════════════════════════════════════ */
function RealBlueprintCard({ num, item }: { num: number; item: InnovationBlueprintItem }) {
  const [copied, setCopied] = useState(false);
  const [riskOpen, setRiskOpen] = useState(false);

  const fmt = (n: number) =>
    "Rp " + n.toLocaleString("id-ID");

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(item.whatsapp_copy_text); } catch { /* fallback */ }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copied for WhatsApp!");
  };

  return (
    <div className="bp-card">
      <div className="bp-card-top">
        <div className="bp-num-badge">{num}</div>
        <span className="bp-category">Innovation Blueprint</span>
        <span className="bp-match">{item.target_location}</span>
      </div>

      <div className="bp-product-row">
        <span className="bp-product-name">{item.title}</span>
      </div>

      <div className="bp-price-section">
        <p className="bp-section-label">Price Comparison</p>
        <div className="bp-price-row">
          <div className="bp-price-col our">
            <span className="bp-price-tag">OUR RECOMMENDATION</span>
            <strong className="bp-price-val">{fmt(item.recommended_price)}</strong>
          </div>
          <span className="bp-vs">vs</span>
          <div className="bp-price-col comp">
            <span className="bp-price-tag">COMPETITOR CEILING</span>
            <strong className="bp-price-val comp-val">{fmt(item.competitor_price_ceiling)}</strong>
          </div>
        </div>
      </div>

      <div className="bp-why-fits">
        <p className="bp-section-label">WHY THIS IDEA FITS</p>
        <p className="bp-why-body">{item.justification}</p>
      </div>

      {item.risk_factors?.length > 0 && (
        <>
          <button className="bp-risk-toggle" onClick={() => setRiskOpen(!riskOpen)}>
            <AlertTriangle size={13} /> Business Risk Factors
            <ChevronDown size={14} style={{ transform: riskOpen ? "rotate(180deg)" : "", transition: ".2s" }} />
          </button>
          {riskOpen && (
            <div className="bp-risk-body">
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {item.risk_factors.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </>
      )}

      <button className="bp-whatsapp-btn" onClick={handleCopy}>
        <MessageCircle size={16} /> {copied ? "Copied!" : "Copy for WhatsApp"} <Copy size={14} />
      </button>
    </div>
  );
}

function Lab() {
  const item = loadCurrentAnalysis();
  const blueprints: InnovationBlueprintItem[] = item?.analysis?.innovation_blueprint || [];

  return (
    <Shell>
      <div className="lab-page">
        <div className="lab-header">
          <div className="lab-model-badge">
            <Sparkles size={13} /> Innovation Lab — sioslo-model · Local AI
          </div>
          <h1 className="lab-title">Your Product Innovation Blueprint</h1>
          <p className="lab-sub">
            {item
              ? <>Ideas based on <em>{item.filename}</em> — click <em>'Copy for WhatsApp'</em> to promote right away!</>
              : "Upload a CSV and run an analysis to generate your innovation blueprint."}
          </p>
        </div>

        {blueprints.length > 0 ? (
          <div className="lab-cards-grid">
            {blueprints.map((bp, i) => (
              <RealBlueprintCard key={bp.id} num={i + 1} item={bp} />
            ))}
          </div>
        ) : (
          <div className="lab-empty">
            <Sparkles size={40} className="lab-empty-icon" />
            <h2>No blueprint yet</h2>
            <p>Upload your sales CSV and run a full analysis to see AI-generated product innovation ideas here.</p>
            <Link href="/upload" className="db-btn-primary" style={{ marginTop: 16 }}>
              <Upload size={15} /> Upload CSV to Start
            </Link>
          </div>
        )}
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   ANALYSIS RESULT PAGE
═══════════════════════════════════════════════ */
function AnalysisPage() {
  const item = loadCurrentAnalysis();
  return (
    <Shell>
      <div className="db-page-head">
        <div>
          <span className="db-mini-kicker">Analysis result</span>
          <h1>{item?.filename || "Latest analysis"}</h1>
          <p className="db-page-sub">Your CSV has been processed through the full SiOslo pipeline.</p>
        </div>
        <Link className="db-btn-primary" href="/dashboard">
          Back to Dashboard <ChevronRight size={15} />
        </Link>
      </div>
      {item ? (
        <section className="analysis-result-section">
          <div className="db-section-head" style={{ marginBottom: 14 }}>
            <h2>Latest Analysis</h2>
            <span className="db-complete-chip"><CheckCircle2 size={14} /> {item.analysis.status}</span>
          </div>
          <div className="ar-metrics">
            <div><span>Reliability</span><strong>{item.analysis.data_health.reliability_score}/100</strong></div>
            <div><span>Keyword overlap</span><strong>{Math.round((item.analysis.correlation_metrics.keyword_overlap_score || 0) * 100)}%</strong></div>
            <div><span>Trend growth</span><strong>{item.analysis.correlation_metrics.market_trend_growth}</strong></div>
          </div>
          <div className="ar-ideas">
            {item.analysis.innovation_blueprint?.map((bp) => (
              <article className="ar-idea" key={bp.id}>
                <Sparkles size={18} />
                <div>
                  <span>Innovation blueprint</span>
                  <h3>{bp.title}</h3>
                  <p>{bp.description || bp.data_justification || "Grounded recommendation from the local model."}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : (
        <section className="analysis-result-section">
          <h2>No analysis selected</h2>
          <p className="db-page-sub">Return to the Dashboard and run an analysis or open a saved report.</p>
          <Link className="db-btn-primary" href="/upload">Upload CSV</Link>
        </section>
      )}
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   SIMULATION PAGE
═══════════════════════════════════════════════ */
function Simulation() {
  const item = loadCurrentAnalysis();

  return (
    <Shell>
      <div className="sim-page" style={{ textAlign: "center", paddingBottom: "40px" }}>
        {/* Header */}
        <div className="lab-model-badge" style={{ marginBottom: "16px" }}>
          <Zap size={13} /> Scenario Analysis
        </div>
        <h1 className="lab-title">Pricing Scenarios</h1>
        <p className="lab-sub" style={{ marginBottom: "40px" }}>
          Three pricing strategies based on your data — pick the one that fits your goal.
        </p>

        {/* Pricing Cards */}
        <div className="sim-cards-grid">
          {/* Conservative Card */}
          <div className="sim-card">
            <h3 className="sim-card-title">Conservative</h3>
            <div className="sim-row mt-4">
              <span className="sim-label">Sell Price</span>
              <span className="sim-val">Rp 13.500</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">COGS</span>
              <span className="sim-val">Rp 10.000</span>
            </div>
            <div className="sim-row mb-4">
              <span className="sim-label">Qty</span>
              <span className="sim-val">100 pcs</span>
            </div>
            <div className="sim-divider" />
            <div className="sim-row mt-4">
              <span className="sim-label">Gross Margin</span>
              <span className="sim-val highlight">25.9%</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Revenue</span>
              <span className="sim-val">Rp 1.350.000</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Est. Profit</span>
              <span className="sim-val highlight-profit">Rp 350.000</span>
            </div>
          </div>

          {/* Recommended Card (AI) */}
          <div className="sim-card recommended">
            <div className="sim-card-header">
              <h3 className="sim-card-title">Recommended</h3>
              <span className="sim-ai-badge">AI Pick</span>
            </div>
            <div className="sim-row mt-4">
              <span className="sim-label">Sell Price</span>
              <span className="sim-val">Rp 15.800</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">COGS</span>
              <span className="sim-val">Rp 10.000</span>
            </div>
            <div className="sim-row mb-4">
              <span className="sim-label">Qty</span>
              <span className="sim-val">90 pcs</span>
            </div>
            <div className="sim-divider" />
            <div className="sim-row mt-4">
              <span className="sim-label">Gross Margin</span>
              <span className="sim-val highlight">36.7%</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Revenue</span>
              <span className="sim-val">Rp 1.422.000</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Est. Profit</span>
              <span className="sim-val highlight-profit">Rp 522.000</span>
            </div>
          </div>

          {/* Premium Card */}
          <div className="sim-card">
            <h3 className="sim-card-title">Premium</h3>
            <div className="sim-row mt-4">
              <span className="sim-label">Sell Price</span>
              <span className="sim-val">Rp 18.000</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">COGS</span>
              <span className="sim-val">Rp 10.000</span>
            </div>
            <div className="sim-row mb-4">
              <span className="sim-label">Qty</span>
              <span className="sim-val">70 pcs</span>
            </div>
            <div className="sim-divider" />
            <div className="sim-row mt-4">
              <span className="sim-label">Gross Margin</span>
              <span className="sim-val highlight">44.4%</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Revenue</span>
              <span className="sim-val">Rp 1.260.000</span>
            </div>
            <div className="sim-row">
              <span className="sim-label">Est. Profit</span>
              <span className="sim-val highlight-profit">Rp 560.000</span>
            </div>
          </div>
        </div>
        
        <p className="sim-footer-note mt-8">
          Based on your historical COGS average — JABODETABEK market rates Q2 2026
        </p>
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   AI BUDDY PAGE
═══════════════════════════════════════════════ */
function AiBuddy() {
  return (
    <Shell>
      <div className="buddy-page" style={{ textAlign: "center" }}>
        <h1 className="lab-title">AI Mentor Chat</h1>
        <p className="lab-sub" style={{ marginBottom: "32px" }}>
          Ask anything about your business strategy, or product ideas — MAC Buddy is ready to answer!
        </p>

        <div className="buddy-chat-container">
          {/* Chat Header */}
          <div className="buddy-chat-header">
            <div className="buddy-avatar">
              <Sparkles size={16} />
            </div>
            <div className="buddy-header-text">
              <h4>MAC Buddy</h4>
              <span className="status-online"><span className="dot"></span> Online · Ready to help your business</span>
            </div>
          </div>

          {/* Chat Body */}
          <div className="buddy-chat-body">
            <div className="chat-message bot">
              <div className="chat-bubble">
                <p><strong>Hi! I'm MAC Buddy, your business AI Mentor ✨</strong></p>
                <p>I'm here to help you think through strategy and scale your F&B business. I've analyzed your latest data — what would you like to discuss first?</p>
              </div>
            </div>
          </div>

          {/* Chat Suggestions */}
          <div className="buddy-suggestions">
            <button className="suggestion-chip">How do I improve below-average items?</button>
            <button className="suggestion-chip">What is the best time to launch a holiday product?</button>
          </div>

          {/* Chat Input */}
          <div className="buddy-input-area">
            <input type="text" placeholder="Type your business question..." className="buddy-input" />
            <button className="buddy-send-btn">
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </Shell>
  );
}

/* ═══════════════════════════════════════════════
   APP ROUTER
═══════════════════════════════════════════════ */
function App() {
  return (
    <>
      <Toaster theme="dark" position="bottom-right" />
      <Switch>
        <Route path="/" component={Landing} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/upload" component={UploadPage} />
        <Route path="/health" component={Health} />
        <Route path="/lab" component={Lab} />
        <Route path="/analysis" component={AnalysisPage} />
        <Route path="/simulation" component={Simulation} />
        <Route path="/buddy" component={AiBuddy} />      
        <Route component={Landing} />
      </Switch>
    </>
  );
}

export default App;