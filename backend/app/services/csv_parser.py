# app/services/csv_parser.py
import pandas as pd
from io import BytesIO
from typing import Tuple, List

# ==================================================
# Fungsi untuk endpoint Sales (upload CSV sederhana)
# ==================================================
def parse_sales_csv(content: bytes, filename: str) -> dict:
    """
    Placeholder untuk Jay – parsing CSV menjadi struktur list of dict
    untuk disimpan ke database via endpoint Sales.
    """
    df = pd.read_csv(BytesIO(content))

    mapped_items = []
    for _, row in df.iterrows():
        mapped_items.append({
            "product_name": row.get("nama_produk") or row.get("product_name", "Unknown"),
            "category": row.get("kategori") or row.get("category", "Uncategorized"),
            "qty_sold": int(row.get("terjual_bulan_ini") or row.get("qty_sold", 0)),
            "remaining_stock": int(row.get("sisa_stok") or row.get("remaining_stock", 0))
        })

    return {
        "filename": filename,
        "total_rows": len(mapped_items),
        "items": mapped_items
    }


# ==================================================
# Fungsi untuk endpoint Analyze (orkestrasi utama)
# ==================================================
def parse_and_validate_csv(file_path: str) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Placeholder untuk Jay – membaca CSV dari path, validasi kolom baku,
    membersihkan data, menghitung data_reliability_score.

    Return:
        - cleaned_df (pd.DataFrame)
        - reliability_score (int, 0-100)
        - warnings (List[str])
    """
    # Baca CSV mentah
    df = pd.read_csv(file_path)

    # TODO: validasi kolom wajib, bersihkan nilai kosong, deteksi outlier, dll.
    # Untuk placeholder, kita asumsikan data selalu valid.
    reliability_score = 85  # dummy
    warnings = ["Kolom kategori kosong di beberapa baris"]  # dummy

    # Pastikan kolom standar ada (placeholder: rename jika perlu)
    # Misalnya, jika kolom 'nama_produk' ada, biarkan; jika 'product_name', rename ke 'nama_produk'
    if "product_name" in df.columns and "nama_produk" not in df.columns:
        df = df.rename(columns={"product_name": "nama_produk"})
    # Tambahkan mapping serupa untuk kolom lain jika diperlukan

    return df, reliability_score, warnings