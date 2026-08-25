from __future__ import annotations

import argparse
import os
import random
import sys

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("psycopg2-binary belum terinstall. Jalankan: pip install psycopg2-binary --break-system-packages")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv belum terinstall. Jalankan: pip install python-dotenv --break-system-packages")
    sys.exit(1)

random.seed(42)

CREATE_DEMOGRAPHICS_SQL = """
CREATE TABLE IF NOT EXISTS demographics (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    segment_name TEXT NOT NULL,
    keywords TEXT NOT NULL,
    age_group TEXT,
    source TEXT,
    recorded_at DATE NOT NULL DEFAULT CURRENT_DATE
);
"""

CREATE_COMPETITOR_PRICES_SQL = """
CREATE TABLE IF NOT EXISTS competitor_prices (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    product_name TEXT NOT NULL,
    competitor_name TEXT NOT NULL,
    price NUMERIC NOT NULL CHECK (price > 0),
    recorded_at DATE NOT NULL DEFAULT CURRENT_DATE
);
"""

# source="riset_2026" -> berbasis riset manual tren UMKM 2026 (lihat docstring atas)
# source lain (TikTok/Instagram/Pinterest) -> asumsi platform tren umum, bukan hasil scraping
DEMOGRAPHICS_ROWS = [
    ("Fashion", "Gen Z Pecinta Warna Pastel", "pastel oversized kaos tie-dye", "16-24", "TikTok"),
    ("Fashion", "Milenial Kerja Hybrid", "kemeja formal casual blazer", "25-35", "Instagram"),
    ("Fashion", "Pecinta Sustainable Fashion", "sustainable thrift upcycle denim ramah lingkungan", "20-30", "riset_2026"),
    ("Fashion", "Modest Wear Modern", "hijab modest wear muslim kasual stylish", "20-35", "riset_2026"),
    ("Fashion", "Gen Z Athleisure", "athleisure legging olahraga kasual nyaman", "16-28", "riset_2026"),
    ("Aksesoris", "Gen Z Nostalgia Y2K", "y2k tas kanvas retro chunky", "16-24", "TikTok"),
    ("Aksesoris", "Pekerja Kantoran Minimalis", "minimalis tas kulit dompet slim", "25-40", "Pinterest"),
    ("Makanan & Minuman", "Gen Z Pecinta Kopi Kekinian", "kopi susu boba matcha kekinian", "17-27", "TikTok"),
    ("Makanan & Minuman", "Keluarga Sehat Rumahan", "sehat organik rendah gula frozen food", "28-45", "Instagram"),
    ("Kosmetik & Skincare", "Gen Z Skincare Enthusiast", "skincare glowing serum sunscreen viral", "16-26", "TikTok"),
    ("Kosmetik & Skincare", "Milenial Clean Beauty", "clean beauty organik cruelty-free", "25-38", "Instagram"),
    ("Kosmetik & Skincare", "Natural Glow Peptide", "natural glow peptide serum vegan tropis", "18-32", "riset_2026"),
    ("Elektronik", "Gen Z Gadget Lover", "gadget wireless earbuds fast charging", "18-28", "TikTok"),
    ("Elektronik", "Pekerja WFH Produktif", "aksesoris laptop ergonomis produktivitas", "25-40", "Pinterest"),
]

# Harga mengacu kisaran pasar nyata dari riset (kaos lokal Rp50rb-90rb: BigGo/Suara.com,
# tas/dompet UMKM Rp150rb-400rb: UKMIndonesia.id & Merdeka.com, kopi kekinian Rp15rb-25rb:
# pengamatan pasar umum). Nama toko FIKTIF, bukan brand asli.
COMPETITOR_PRICES_ROWS = [
    ("Fashion", "Kaos Polos Distro", "Distro Karya Lokal", 65000),
    ("Fashion", "Kaos Polos Distro", "Kedai Sablon Nusantara", 75000),
    ("Fashion", "Kemeja Formal", "Butik Rapi Jaya", 145000),
    ("Fashion", "Jaket Denim", "Gudang Denim Kita", 210000),
    ("Fashion", "Hijab Modest Wear", "Griya Hijab Kekinian", 95000),
    ("Aksesoris", "Tas Kanvas", "Kriya Tas Handmade", 185000),
    ("Aksesoris", "Tas Rajut Handmade", "Rajut Estetik Kriya", 245000),
    ("Aksesoris", "Dompet Kulit", "Kulit Asli Studio", 175000),
    ("Makanan & Minuman", "Kopi Susu Kemasan", "Kedai Kopi Rasa", 18000),
    ("Makanan & Minuman", "Snack Sehat Kemasan", "Dapur Sehat Rumahan", 25000),
    ("Kosmetik & Skincare", "Serum Wajah", "Klinik Cantik Lokal", 85000),
    ("Kosmetik & Skincare", "Sunscreen SPF50", "Skin Studio Nusantara", 62000),
    ("Elektronik", "Wireless Earbuds", "Gadget Hemat Store", 245000),
    ("Elektronik", "Powerbank 10000mAh", "Elektronik Rakyat", 140000),
]


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print(
            "ERROR: DATABASE_URL belum diset. Contoh format (session pooler):\n"
            "  postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres"
        )
        sys.exit(1)
    try:
        return psycopg2.connect(database_url)
    except psycopg2.OperationalError as e:
        print(f"ERROR: gagal connect ke Postgres.\nDetail: {e}")
        sys.exit(1)


def _table_is_empty(cur, table_name: str) -> bool:
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cur.fetchone()[0] == 0


def seed_demographics(cur, force: bool = False):
    if not force and not _table_is_empty(cur, "demographics"):
        print("-> demographics: sudah terisi, skip (pakai --reset untuk isi ulang).")
        return
    execute_values(cur, "INSERT INTO demographics (category, segment_name, keywords, age_group, source) VALUES %s", DEMOGRAPHICS_ROWS)
    print(f"-> demographics: {len(DEMOGRAPHICS_ROWS)} baris dummy ditambahkan.")


def seed_competitor_prices(cur, force: bool = False):
    if not force and not _table_is_empty(cur, "competitor_prices"):
        print("-> competitor_prices: sudah terisi, skip (pakai --reset untuk isi ulang).")
        return
    execute_values(cur, "INSERT INTO competitor_prices (category, product_name, competitor_name, price) VALUES %s", COMPETITOR_PRICES_ROWS)
    print(f"-> competitor_prices: {len(COMPETITOR_PRICES_ROWS)} baris dummy ditambahkan.")


def main():
    parser = argparse.ArgumentParser(description="Seed dummy data untuk demographics & competitor_prices.")
    parser.add_argument("--reset", action="store_true", help="Kosongkan tabel dulu sebelum insert ulang.")
    args = parser.parse_args()

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_DEMOGRAPHICS_SQL)
                cur.execute(CREATE_COMPETITOR_PRICES_SQL)

                if args.reset:
                    print("--reset: mengosongkan tabel dummy terlebih dahulu...")
                    cur.execute("TRUNCATE TABLE demographics RESTART IDENTITY;")
                    cur.execute("TRUNCATE TABLE competitor_prices RESTART IDENTITY;")

                seed_demographics(cur, force=args.reset)
                seed_competitor_prices(cur, force=args.reset)

        print("\nSeeding selesai.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
