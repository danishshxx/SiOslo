import sys
from pathlib import Path

import csv
from pathlib import Path
from datetime import datetime, date
import random

from app.core.database import SessionLocal
from app.models.market import MarketTrend, Demographic, CompetitorPrice

sys.path.insert(0, str(Path(__file__).parent.parent))

# Lokasi output scraper
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

def parse_date(date_str: str) -> date:
    """Parse tanggal dari string CSV, fallback ke hari ini."""
    if not date_str:
        return datetime.now().date()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return datetime.now().date()

def import_market_trends(csv_path: Path, db) -> int:
    """Import CSV market_trends.csv ke tabel market_trends."""
    if not csv_path.exists():
        print(f"❌ File {csv_path} tidak ditemukan, lewati.")
        return 0

    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trend = MarketTrend(
                keyword=row.get("keyword", "").strip(),
                volume=int(row.get("volume", 0)),
                source=row.get("source", "scraper"),
                date=parse_date(row.get("date", "")),
            )
            db.add(trend)
            count += 1
    db.commit()
    print(f"✅ {count} baris market_trends diimpor.")
    return count

def import_demographics(csv_path: Path, db) -> int:
    """Import CSV demographics.csv ke tabel demographics."""
    if not csv_path.exists():
        print(f"❌ File {csv_path} tidak ditemukan, lewati.")
        return 0

    count = 0
    age_groups = ["18-24", "25-34", "35-44", "45+"]
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            demo = Demographic(
                category=row.get("category", "").strip(),
                segment_name=row.get("segment_name", "").strip(),
                keywords=row.get("keywords", "").strip(),
                age_group=row.get("age_group") or random.choice(age_groups),
                source=row.get("source", "scraper"),
                recorded_at=parse_date(row.get("recorded_at", "")),
            )
            db.add(demo)
            count += 1
    db.commit()
    print(f"✅ {count} baris demographics diimpor.")
    return count

def import_competitor_prices(csv_path: Path, db) -> int:
    """Import CSV competitor_prices.csv ke tabel competitor_prices."""
    if not csv_path.exists():
        print(f"❌ File {csv_path} tidak ditemukan, lewati.")
        return 0

    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comp = CompetitorPrice(
                category=row.get("category", "").strip(),
                product_name=row.get("product_name", "").strip(),
                competitor_name=row.get("competitor_name", "").strip(),
                price=float(row.get("price", 0)),
                recorded_at=parse_date(row.get("recorded_at", "")),
            )
            db.add(comp)
            count += 1
    db.commit()
    print(f"✅ {count} baris competitor_prices diimpor.")
    return count

def main():
    print("=== Import CSV ke Database SiOslo ===")
    market_csv = OUTPUT_DIR / "market_trends.csv"
    demographics_csv = OUTPUT_DIR / "demographics.csv"
    competitor_csv = OUTPUT_DIR / "competitor_prices.csv"

    db = SessionLocal()
    try:
        total = 0
        total += import_market_trends(market_csv, db)
        total += import_demographics(demographics_csv, db)
        total += import_competitor_prices(competitor_csv, db)
        print(f"\n🎉 Total {total} baris data berhasil diimpor ke database.")
    except Exception as e:
        db.rollback()
        print(f"❌ Gagal impor: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()