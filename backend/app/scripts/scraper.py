import csv
import random
import re
from datetime import datetime
from pathlib import Path

import feedparser


# ---------- KONFIGURASI ----------
RSS_FEEDS = [
    ("CNN Indonesia", "https://www.cnnindonesia.com/ekonomi/rss"),
    ("CNBC Indonesia", "https://www.cnbcindonesia.com/news/rss"),
    ("Antara News", "https://www.antaranews.com/rss/terkini"),
]

CATEGORY_KEYWORDS = {
    "Minuman": [
        "minuman", "kopi", "teh", "jus", "susu", "es", "matcha",
        "boba", "soda", "sirup", "wedang", "cokelat panas"
    ],
    "Makanan Ringan": [
        "makanan ringan", "cemilan", "snack", "jajanan", "camilan",
        "keripik", "roti", "kue", "cokelat", "pedas", "gurih",
        "basreng", "makaroni", "singkong"
    ],
    "Makanan Berat": [
        "makanan berat", "nasi", "ayam", "mie", "geprek", "sushi",
        "burger", "pizza", "steak", "rendang", "soto", "bakso"
    ],
    "Fashion": [
        "fashion", "pakaian", "outfit", "style", "mode", "trend baju",
        "y2k", "streetwear", "hijab", "batik", "sepatu", "tas", "kemeja"
    ],
    "Aksesoris": [
        "aksesoris", "tas", "jam tangan", "perhiasan", "topi",
        "kacamata", "dompet", "ikat pinggang", "kalung", "gelang"
    ],
    "Kecantikan": [
        "skincare", "makeup", "kosmetik", "beauty", "serum",
        "lipstik", "bedak", "parfum", "sabun", "shampoo"
    ],
}

PRODUCT_EXAMPLES = {
    "Minuman": [
        "Kopi Susu Aren", "Es Teh Kampul", "Boba Brown Sugar",
        "Matcha Latte", "Wedang Jahe", "Jus Alpukat"
    ],
    "Makanan Ringan": [
        "Keripik Singkong Pedas", "Basreng", "Makaroni Bantet",
        "Roti Bakar Cokelat", "Kue Cubit", "Cireng Isi"
    ],
    "Makanan Berat": [
        "Ayam Geprek", "Nasi Goreng Seafood", "Mie Gacoan",
        "Sushi Roll", "Burger Wagyu", "Soto Betawi"
    ],
    "Fashion": [
        "Kaos Oversize Polos", "Kemeja Flanel", "Hijab Voal Premium",
        "Sepatu Sneakers", "Tas Ransel", "Celana Cargo"
    ],
    "Aksesoris": [
        "Jam Tangan Minimalis", "Kalung Titanium", "Gelang Etnik",
        "Dompet Kulit", "Kacamata UV", "Topi Baseball"
    ],
    "Kecantikan": [
        "Serum Vitamin C", "Lipstik Matte", "Bedak Tabur",
        "Parfum Eau de Toilette", "Sabun Wajah Tea Tree"
    ],
}

PRICE_RANGES = {
    "Minuman": (8_000, 35_000),
    "Makanan Ringan": (5_000, 25_000),
    "Makanan Berat": (15_000, 50_000),
    "Fashion": (80_000, 400_000),
    "Aksesoris": (50_000, 300_000),
    "Kecantikan": (30_000, 250_000),
}

STOPWORDS = {
    "dan", "di", "ke", "dari", "yang", "untuk", "dengan", "lewat", "imbas",
    "dalam", "ini", "itu", "pada", "sebagai", "oleh", "karena", "saat",
    "setelah", "hingga", "atau", "juga", "jadi", "sudah", "bisa", "akan",
    "buat", "ada", "tidak", "belum", "vs"
}

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------- FUNGSI UTAMA ----------
def clean_title(title: str) -> str:
    """Hapus tag HTML & karakter aneh dari judul, kembalikan huruf kecil."""
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title


def detect_category(title_clean: str) -> str | None:
    """Deteksi kategori menggunakan kata utuh (word boundary)."""
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}\b", title_clean):
                return cat
    return None


def extract_keywords_from_title(title_clean: str, category: str) -> list[str]:
    """Ekstrak keyword bersih tanpa kata sambung (stopwords)."""
    words = title_clean.split()
    found = set()

    for kw in CATEGORY_KEYWORDS[category]:
        if re.search(rf"\b{re.escape(kw)}\b", title_clean):
            found.add(kw)

    filtered_words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    if len(filtered_words) >= 2:
        found.add(f"{filtered_words[0]} {filtered_words[1]}")
    elif len(filtered_words) == 1:
        found.add(filtered_words[0])

    return list(found)[:3]


def fetch_articles(max_per_feed: int = 20) -> list[dict]:
    """Ambil artikel relevan dari RSS, dedupe berdasarkan judul."""
    articles = []
    seen_titles = set()

    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries[:max_per_feed]:
                raw_title = entry.get("title", "")
                title_clean = clean_title(raw_title)

                if not title_clean or title_clean in seen_titles:
                    continue

                category = detect_category(title_clean)
                if not category:
                    continue

                seen_titles.add(title_clean)
                articles.append({
                    "title_clean": title_clean,
                    "source": source_name,
                    "category": category,
                    "link": entry.get("link", ""),
                })
                count += 1
        except Exception as e:
            print(f"Gagal fetch {feed_url}: {e}")

    return articles


def generate_market_trends(articles: list[dict]) -> list[dict]:
    """Buat data market_trends dari keyword unik di artikel."""
    rows = []
    for a in articles:
        keywords = extract_keywords_from_title(a["title_clean"], a["category"])
        for kw in keywords:
            freq = sum(
                1 for other in articles
                if kw in " ".join(extract_keywords_from_title(other["title_clean"], other["category"]))
            )
            volume = random.randint(20, 500) + (freq * 50)
            rows.append({
                "keyword": kw,
                "volume": volume,
                "source": a["source"],
                "date": datetime.now().strftime("%Y-%m-%d"),
            })
    return rows


def generate_market_trends_fallback() -> list[dict]:
    """Fallback: buat market_trends dari kata kunci kategori."""
    rows = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords[:5]:
            for _ in range(random.randint(2, 5)):
                rows.append({
                    "keyword": kw,
                    "volume": random.randint(500, 80_000),
                    "source": "synthetic",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })
    return rows


def generate_demographics(articles: list[dict]) -> list[dict]:
    """Buat data demographics dari kategori & keyword berita."""
    rows = []
    for a in articles:
        category = a["category"]
        keywords = extract_keywords_from_title(a["title_clean"], category)
        segment_name = f"Segmen {category} {len(rows)+1}"
        rows.append({
            "category": category,
            "segment_name": segment_name,
            "keywords": ", ".join(keywords),
            "source": a["source"],
        })
    return rows


def generate_demographics_fallback() -> list[dict]:
    """Fallback: buat demographics dari kategori & keyword."""
    rows = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        selected = ", ".join(keywords[:5])
        for i in range(3):
            rows.append({
                "category": category,
                "segment_name": f"Segmen {category} {i+1}",
                "keywords": selected,
                "source": "synthetic",
            })
    return rows


def generate_competitor_prices(articles: list[dict]) -> list[dict]:
    """Buat data competitor_prices dari produk contoh per kategori."""
    rows = []
    categories = {a["category"] for a in articles if "category" in a}
    if not categories:
        categories = set(PRICE_RANGES.keys())

    for category in categories:
        products = PRODUCT_EXAMPLES.get(category, [])
        if not products:
            continue
        low, high = PRICE_RANGES.get(category, (10_000, 100_000))
        for product in products:
            for _ in range(random.randint(3, 5)):
                rows.append({
                    "category": category,
                    "product_name": product,
                    "competitor_name": f"Toko Kompetitor {random.randint(100, 999)}",
                    "price": random.randint(low, high),
                    "source": "synthetic",
                })
    return rows


def save_to_csv(rows: list[dict], filename: str):
    if not rows:
        print(f"Tidak ada data untuk {filename}")
        return
    keys = rows[0].keys()
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ {filepath} ({len(rows)} baris)")


# ---------- MAIN ----------
if __name__ == "__main__":
    print("=== SiOslo Seed Data Generator ===")
    print("Fetching RSS feeds...")
    articles = fetch_articles(max_per_feed=20)
    print(f"Total artikel relevan: {len(articles)}")

    if len(articles) < 10:
        print("Artikel relevan kurang dari 10, gunakan fallback sintetik.")
        market_trends = generate_market_trends_fallback()
        demographics = generate_demographics_fallback()
        # Untuk competitor, buat artikel dummy dari semua kategori
        articles = [
            {"title_clean": "default", "source": "synthetic", "category": cat}
            for cat in PRICE_RANGES.keys()
        ]
    else:
        market_trends = generate_market_trends(articles)
        demographics = generate_demographics(articles)

    competitor_prices = generate_competitor_prices(articles)

    save_to_csv(market_trends, "market_trends.csv")
    save_to_csv(demographics, "demographics.csv")
    save_to_csv(competitor_prices, "competitor_prices.csv")
    print("\nSemua CSV siap masuk ke PostgreSQL!")
