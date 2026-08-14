"""
csv_parser.py
=================================================================
Modul Data Ingestion & Guardrails untuk Market-Driven R&D Buddy.
Tanggung jawab: Jay (Data Ingestion & Guardrails Specialist)

Tugas modul ini HANYA dua hal (sengaja dibatasi, sesuai aturan MVP
"sinkron, tanpa background job"):
    1. Membaca & membersihkan CSV penjualan yang diunggah user.
    2. Menghitung `data_reliability_score` (0-100) secara DETERMINISTIK
       dan TRANSPARAN (ada breakdown, bukan angka ajaib).

Modul ini TIDAK memanggil FastAPI, TIDAK memanggil database, dan TIDAK
memanggil LLM. Fungsi inti `parse_and_validate()` murni Python biasa ->
bisa di-unit-test sendiri tanpa perlu jalankan seluruh stack Docker.

Tiga fungsi publik, tiga konsumen berbeda:
    - parse_and_validate(source) -> dict
      Engine inti. Dipakai internal oleh dua wrapper di bawah.
    - parse_sales_csv(content: bytes, filename: str) -> dict
      Dipakai app/api/v1/endpoints/sales.py (endpoint /sales/upload).
    - parse_and_validate_csv(filepath_or_bytes) -> tuple[DataFrame, int, list[str]]
      Dipakai app/api/v1/endpoints/analyze.py (endpoint /analyze/).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from typing import Optional, Union

import pandas as pd

# =================================================================
# 1. KONFIGURASI SKEMA (satu-satunya sumber kebenaran nama kolom)
# =================================================================

REQUIRED_COLUMNS = [
    "transaction_date",
    "product_name",
    "category",
    "qty_sold",
    "remaining_stock",
    "unit_price",
]

NUMERIC_COLUMNS = ["qty_sold", "remaining_stock", "unit_price"]
TEXT_LABEL_COLUMNS = ["product_name", "category"]

# Alias -> nama baku bahasa Inggris (SEPAKAT TIM: variabel internal Inggris,
# persis sama dengan nama kolom di Postgres). Kunci alias tetap menerima
# header Indonesia ATAU Inggris -- karena user (UMKM) tetap boleh mengisi
# CSV dengan header Indonesia yang natural buat mereka, tapi begitu masuk
# ke sistem, semua otomatis diterjemahkan ke nama Inggris di titik ini SAJA.
# Kunci HARUS huruf kecil & sudah di-strip whitespace.
COLUMN_ALIASES: dict[str, str] = {
    "tanggal": "transaction_date",
    "date": "transaction_date",
    "transaction_date": "transaction_date",
    "nama produk": "product_name",
    "nama_produk": "product_name",
    "produk": "product_name",
    "product_name": "product_name",
    "product": "product_name",
    "kategori": "category",
    "category": "category",
    "terjual": "qty_sold",
    "terjual bulan ini": "qty_sold",
    "terjual_bulan_ini": "qty_sold",
    "qty_sold": "qty_sold",
    "qty sold": "qty_sold",
    "sisa stok": "remaining_stock",
    "sisa_stok": "remaining_stock",
    "stok sisa": "remaining_stock",
    "remaining_stock": "remaining_stock",
    "stok": "remaining_stock",
    "harga satuan": "unit_price",
    "harga_satuan": "unit_price",
    "harga": "unit_price",
    "price": "unit_price",
    "unit_price": "unit_price",
}

MISSING_VALUE_TOKENS = {
    "", "nan", "n/a", "na", "-", "--", "kosong", "tidak ada",
    "?", "null", "none", "unknown", "tidak diketahui",
}

FORMULA_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

ENCODING_CASCADE = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]

MIN_ROWS = 1
MAX_ROWS = 50_000


# =================================================================
# 2. STRUKTUR HASIL
# =================================================================

@dataclass
class ValidationIssue:
    row_index: Optional[int]
    column: Optional[str]
    issue_type: str
    detail: str


@dataclass
class DataHealthReport:
    reliability_score: int
    status_color: str
    warning_message: str
    score_breakdown: dict = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)


# =================================================================
# 3. LAPISAN BACA FILE (encoding + delimiter sniffing)
# =================================================================

def _read_raw_bytes(source: Union[str, bytes, io.IOBase]) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, str):
        with open(source, "rb") as f:
            return f.read()
    return source.read()


def _decode_with_cascade(raw: bytes) -> tuple[str, str]:
    last_error = None
    for enc in ENCODING_CASCADE:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError as e:
            last_error = e
            continue
    raise ValueError(
        f"Tidak bisa membaca file dengan encoding apa pun dari {ENCODING_CASCADE}. "
        f"Error terakhir: {last_error}"
    )


def _sniff_delimiter(sample_text: str) -> str:
    header_line = sample_text.strip().splitlines()[0] if sample_text.strip() else ""
    candidates = [",", ";", "\t"]
    try:
        dialect = csv.Sniffer().sniff(sample_text[:4096], delimiters="".join(candidates))
        return dialect.delimiter
    except csv.Error:
        counts = {d: header_line.count(d) for d in candidates}
        best = max(counts, key=counts.get)
        return best if counts[best] > 0 else ","


# =================================================================
# 4. PEMBERSIHAN NILAI
# =================================================================

def _normalize_column_name(col: str) -> str:
    return re.sub(r"\s+", " ", str(col).strip().lower())


def normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    rename_map = {}
    unknown = []
    for col in df.columns:
        key = _normalize_column_name(col)
        if key in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[key]
        else:
            unknown.append(col)
    return df.rename(columns=rename_map), unknown


def _is_missing_token(value) -> bool:
    if pd.isna(value):
        return True
    return str(value).strip().lower() in MISSING_VALUE_TOKENS


def _sanitize_formula_injection(value):
    if isinstance(value, str) and value.startswith(FORMULA_INJECTION_PREFIXES):
        return "'" + value
    return value


def clean_numeric_value(raw_value) -> Optional[float]:
    if _is_missing_token(raw_value):
        return None

    s = str(raw_value).strip()
    s = re.sub(r"(?i)rp\.?\s*", "", s)
    s = s.replace(" ", "")

    if re.match(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.match(r"^-?\d+,\d+$", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        return float(s)
    except ValueError:
        return None


def parse_date_value(raw_value):
    if _is_missing_token(raw_value):
        return None
    try:
        return pd.to_datetime(raw_value, dayfirst=True, errors="raise")
    except (ValueError, TypeError):
        return None


# =================================================================
# 5. VALIDASI & SCORING
# =================================================================

def _validate_and_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    df = df.copy()

    # -- sanitasi formula injection HANYA di kolom label/teks --
    for col in TEXT_LABEL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(_sanitize_formula_injection)

    # -- kolom numerik (nama Inggris, sesuai REQUIRED_COLUMNS/NUMERIC_COLUMNS) --
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue
        cleaned = df[col].map(clean_numeric_value)
        for idx, (orig, val) in enumerate(zip(df[col], cleaned)):
            if pd.isna(val) and not _is_missing_token(orig):
                issues.append(ValidationIssue(idx, col, "bad_numeric",
                                               f"Nilai '{orig}' tidak bisa dibaca sebagai angka"))
            elif pd.isna(val):
                issues.append(ValidationIssue(idx, col, "missing_value",
                                               f"Nilai kosong di kolom '{col}'"))
        df[col] = cleaned

    # -- kolom tanggal (nama Inggris: transaction_date) --
    if "transaction_date" in df.columns:
        cleaned_dates = df["transaction_date"].map(parse_date_value)
        for idx, (orig, val) in enumerate(zip(df["transaction_date"], cleaned_dates)):
            if pd.isna(val) and not _is_missing_token(orig):
                issues.append(ValidationIssue(idx, "transaction_date", "bad_date",
                                               f"Tanggal '{orig}' tidak valid (harap DD/MM/YYYY)"))
            elif pd.isna(val):
                issues.append(ValidationIssue(idx, "transaction_date", "missing_value",
                                               "Tanggal kosong"))
        df["transaction_date"] = cleaned_dates

    # -- outlier: nilai mustahil (nama Inggris) --
    if "remaining_stock" in df.columns:
        neg_mask = df["remaining_stock"] < 0
        for idx in df.index[neg_mask.fillna(False)]:
            issues.append(ValidationIssue(int(idx), "remaining_stock", "outlier",
                                           "Stok negatif (mustahil secara bisnis)"))
    if "qty_sold" in df.columns:
        neg_mask = df["qty_sold"] < 0
        for idx in df.index[neg_mask.fillna(False)]:
            issues.append(ValidationIssue(int(idx), "qty_sold", "outlier",
                                           "Jumlah terjual negatif (mustahil secara bisnis)"))
    if "unit_price" in df.columns:
        bad_price_mask = df["unit_price"] <= 0
        for idx in df.index[bad_price_mask.fillna(False)]:
            issues.append(ValidationIssue(int(idx), "unit_price", "outlier",
                                           "Harga nol atau negatif"))

    # -- duplikat (nama Inggris) --
    if "product_name" in df.columns and "category" in df.columns:
        dup_mask = df.duplicated(subset=["product_name", "category"], keep="first")
        for idx in df.index[dup_mask]:
            issues.append(ValidationIssue(int(idx), "product_name", "duplicate",
                                           "Baris produk duplikat (baris pertama dipakai)"))
        df = df[~dup_mask]

    return df, issues


def compute_reliability_score(total_rows: int, issues: list[ValidationIssue]) -> tuple[int, dict]:
    """
    Formula TERBUKA & DETERMINISTIK (harus sama persis dengan yang ditulis
    di bab Metodologi proposal):

        score = 100
              - (persentase baris bermasalah missing_value/bad_numeric/bad_date) * 40
              - (persentase baris duplicate) * 20
              - (persentase baris outlier) * 40
    """
    if total_rows == 0:
        return 0, {"reason": "Tidak ada baris data untuk dinilai"}

    def pct(issue_types):
        rows = {i.row_index for i in issues if i.issue_type in issue_types and i.row_index is not None}
        return len(rows) / total_rows

    format_penalty = min(pct({"missing_value", "bad_numeric", "bad_date"}) * 40, 40)
    duplicate_penalty = min(pct({"duplicate"}) * 20, 20)
    outlier_penalty = min(pct({"outlier"}) * 40, 40)

    raw_score = 100 - format_penalty - duplicate_penalty - outlier_penalty
    score = max(0, min(100, round(raw_score)))

    breakdown = {
        "base_score": 100,
        "format_issue_penalty": round(format_penalty, 1),
        "duplicate_penalty": round(duplicate_penalty, 1),
        "outlier_penalty": round(outlier_penalty, 1),
        "final_score": score,
    }
    return score, breakdown


def _status_from_score(score: int) -> tuple[str, str]:
    if score >= 70:
        return "green", "Data penjualan sehat dan konsisten. Analisis dapat dilanjutkan."
    if score >= 50:
        return "yellow", "Data memiliki beberapa masalah kecil. Analisis tetap dilanjutkan, hasil mungkin kurang presisi."
    return "red", "Data terlalu banyak masalah untuk dianalisis secara andal. Mohon perbaiki CSV dan unggah ulang."


# =================================================================
# 6. ENGINE INTI
# =================================================================

def parse_and_validate(source: Union[str, bytes, io.IOBase]) -> dict:
    """
    Fungsi murni, tidak bergantung FastAPI/DB/LLM apa pun.
    Selalu mengembalikan dict terstruktur -- TIDAK PERNAH raise exception
    ke pemanggil untuk kondisi data yang buruk (hanya untuk bug internal).
    """
    try:
        raw = _read_raw_bytes(source)
    except FileNotFoundError:
        return _error_response("File tidak ditemukan.")

    if len(raw) == 0:
        return _error_response("File kosong (0 byte).")

    try:
        text, used_encoding = _decode_with_cascade(raw)
    except ValueError as e:
        return _error_response(str(e))

    if not text.strip():
        return _error_response("File tidak memiliki konten.")

    delimiter = _sniff_delimiter(text)

    try:
        df = pd.read_csv(io.StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
    except pd.errors.ParserError as e:
        return _error_response(f"CSV tidak bisa diparse: {e}")

    if df.shape[0] < MIN_ROWS:
        return _error_response("CSV tidak memiliki baris data (hanya header, atau kosong).")
    if df.shape[0] > MAX_ROWS:
        return _error_response(
            f"CSV terlalu besar ({df.shape[0]} baris). Batas MVP: {MAX_ROWS} baris."
        )

    df, unknown_columns = normalize_columns(df)

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        return _error_response(
            "Kolom wajib tidak ditemukan: " + ", ".join(missing_required) +
            ". Pastikan CSV memakai template resmi."
        )

    total_rows_before = df.shape[0]
    cleaned_df, issues = _validate_and_clean(df)

    for col in unknown_columns:
        issues.append(ValidationIssue(None, col, "unknown_column",
                                       f"Kolom '{col}' tidak dikenali, diabaikan"))

    score, breakdown = compute_reliability_score(total_rows_before, issues)
    status_color, message = _status_from_score(score)

    health = DataHealthReport(
        reliability_score=score,
        status_color=status_color,
        warning_message=message,
        score_breakdown=breakdown,
        issues=issues,
    )

    return {
        "status": "success",
        "meta": {
            "encoding_detected": used_encoding,
            "delimiter_detected": delimiter,
            "rows_received": total_rows_before,
            "rows_after_cleaning": int(cleaned_df.shape[0]),
        },
        "data_health": {
            "reliability_score": health.reliability_score,
            "status_color": health.status_color,
            "warning_message": health.warning_message,
            "score_breakdown": health.score_breakdown,
            "issues": [
                {
                    "row_index": i.row_index,
                    "column": i.column,
                    "issue_type": i.issue_type,
                    "detail": i.detail,
                }
                for i in health.issues
            ],
        },
        "cleaned_data": cleaned_df,
    }


def _error_response(message: str) -> dict:
    return {
        "status": "error",
        "meta": {},
        "data_health": {
            "reliability_score": 0,
            "status_color": "red",
            "warning_message": message,
            "score_breakdown": {},
            "issues": [],
        },
        "cleaned_data": None,
    }


# =================================================================
# 7. WRAPPER #1 -- dipakai app/api/v1/endpoints/sales.py
# =================================================================

def parse_sales_csv(content: bytes, filename: str) -> dict:
    """
    Adapter untuk endpoint /sales/upload. Sengaja return bentuk FLAT
    (bukan bentuk kaya parse_and_validate) karena sales.py cuma insert
    4 kolom dasar tanpa fitur data_health -- lihat parse_and_validate_csv()
    di bawah untuk versi yang dipakai /analyze/, yang membawa reliability
    score.

    Return:
        {"filename": str, "total_rows": int, "items": [dict, ...]}
        Setiap item dict: product_name, category, qty_sold, remaining_stock
        (angka NaN dikonversi ke 0 di sini -- lihat catatan NaN di bawah).

    Raises:
        ValueError -- kalau CSV gagal divalidasi (kolom wajib hilang, dst),
        supaya endpoint bisa tangkap dan balikin HTTP 422 yang jelas.
    """
    result = parse_and_validate(content)
    if result["status"] != "success":
        raise ValueError(result["data_health"]["warning_message"])

    df = result["cleaned_data"]
    items = []
    for _, row in df.iterrows():
        # PENTING: row.get("qty_sold", 0) TIDAK cukup -- kalau kolomnya ADA
        # tapi nilainya NaN (baris rusak yang memang didesain lolos ke sini
        # untuk transparansi), .get() tetap mengembalikan NaN, bukan default.
        # Makanya perlu pd.notna() eksplisit di sini.
        qty = row.get("qty_sold")
        stock = row.get("remaining_stock")
        items.append({
            "product_name": row.get("product_name"),
            "category": row.get("category") if pd.notna(row.get("category")) else "Uncategorized",
            "qty_sold": int(qty) if pd.notna(qty) else 0,
            "remaining_stock": int(stock) if pd.notna(stock) else 0,
        })

    return {
        "filename": filename,
        "total_rows": int(result["meta"]["rows_after_cleaning"]),
        "items": items,
    }


# =================================================================
# 8. WRAPPER #2 -- dipakai app/api/v1/endpoints/analyze.py
# =================================================================

def parse_and_validate_csv(filepath_or_bytes: Union[str, bytes]) -> tuple[pd.DataFrame, int, list[str]]:
    """
    Adapter untuk endpoint /analyze/. Return tuple 3 elemen sesuai yang
    di-unpack analyze.py: (cleaned_df, reliability_score, warnings).

    cleaned_df: DataFrame dengan nama kolom Inggris (product_name, category,
                qty_sold, remaining_stock, unit_price, transaction_date),
                masih bisa berisi NaN di baris yang datanya rusak --
                pemanggil (analyze.py) wajib pakai pd.notna() sebelum
                cast ke int/float.
    reliability_score: 0-100
    warnings: list of string, kosong kalau tidak ada isu sama sekali

    Raises:
        ValueError -- kalau CSV gagal divalidasi total (kolom wajib hilang,
        file kosong, dst), supaya endpoint balikin HTTP 422.
    """
    result = parse_and_validate(filepath_or_bytes)
    if result["status"] != "success":
        raise ValueError(result["data_health"]["warning_message"])

    warnings = [issue["detail"] for issue in result["data_health"]["issues"]]

    return (
        result["cleaned_data"],
        result["data_health"]["reliability_score"],
        warnings,
    )


# =================================================================
# 9. DEMO MANDIRI
# =================================================================

if __name__ == "__main__":
    import json

    DIRTY_SAMPLE_CSV = (
        "tanggal;Nama Produk;kategori;terjual_bulan_ini;sisa_stok;harga_satuan\n"
        "01/06/2026;Kaos Polos Neon;Fashion;12;200;Rp65.000\n"
        "01/06/2026;Kaos Polos Neon;Fashion;12;200;Rp65.000\n"
        "02/06/2026;Jaket Denim Lama;Fashion;5;45;180000\n"
        "03/06/2026;Topi Rajut;Aksesoris;-;30;25000\n"
        "2026-06-04;Sandal Jepit;Aksesoris;8;-10;15000\n"
        "05/06/2026;Tas Kanvas;Aksesoris;3;abc;90000\n"
    ).encode("utf-8-sig")

    print("=== DEMO 1: parse_and_validate() (engine inti) ===\n")
    result = parse_and_validate(DIRTY_SAMPLE_CSV)
    printable = {k: v for k, v in result.items() if k != "cleaned_data"}
    print(json.dumps(printable, indent=2, ensure_ascii=False, default=str))

    print("\n=== DEMO 2: parse_sales_csv() (wrapper utk sales.py) ===\n")
    sales_result = parse_sales_csv(DIRTY_SAMPLE_CSV, "test.csv")
    print(json.dumps(sales_result, indent=2, ensure_ascii=False, default=str))

    print("\n=== DEMO 3: parse_and_validate_csv() (wrapper utk analyze.py) ===\n")
    df, score, warnings = parse_and_validate_csv(DIRTY_SAMPLE_CSV)
    print("reliability_score:", score)
    print("warnings:", warnings)
    print(df)