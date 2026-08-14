# File: app/api/v1/endpoints/analyze.py
import uuid
import os
import tempfile
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sales import SalesReport, SalesItem
from app.services.csv_parser import parse_and_validate_csv
from app.services.correlation_engine import calculate_correlation
from app.services.llm_service import generate_innovation_blueprint
from app.schemas.analysis import AnalysisResponse

router = APIRouter(prefix="/analyze", tags=["Analysis"])


def _safe_int(value, default=0):
    """int() polos crash kalau value NaN. .get(key, default) TIDAK menolong
    di sini karena default cuma dipakai kalau key hilang total, bukan kalau
    nilainya ADA tapi NaN -- dan NaN memang skenario yang sengaja didesain
    muncul dari csv_parser.py untuk baris data yang rusak."""
    return int(value) if pd.notna(value) else default


def _safe_float(value, default=None):
    return float(value) if pd.notna(value) else default


def _safe_date(value, default=None):
    if pd.isna(value):
        return default
    return value.date() if hasattr(value, "date") else value


@router.post("/", response_model=AnalysisResponse)
def analyze_sales(
    file: UploadFile = File(...),
    target_lokasi: str = Form(..., description="Daerah target inovasi"),
    session_id: str = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Endpoint Utama: Menerima CSV penjualan, analisis korelasi pasar,
    dan menghasilkan blueprint inovasi produk.
    """
    # 1. Generate session_id jika tidak dikirim
    if not session_id:
        session_id = str(uuid.uuid4())

    # 2. Simpan file CSV ke temporary file (dibutuhkan oleh parser Jay)
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = file.file.read()
            tmp.write(content)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")

    # 3. Panggil CSV Parser Jay (sinkron)
    try:
        cleaned_df, reliability_score, warnings = parse_and_validate_csv(tmp_path)
    except ValueError as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=f"CSV tidak valid: {str(e)}")
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=f"CSV tidak valid: {str(e)}")

    # 4. Simpan data penjualan ke database
    #    Nama kolom di cleaned_df sudah Inggris (product_name, category,
    #    qty_sold, remaining_stock, unit_price, transaction_date) --
    #    JANGAN pakai nama Indonesia lama (nama_produk, dst), itu sudah
    #    tidak ada lagi sejak csv_parser.py di-refactor.
    try:
        report = SalesReport(
            filename=file.filename,
            total_rows=len(cleaned_df)
        )
        db.add(report)
        db.flush()  # supaya report.id tersedia sebelum commit

        for _, row in cleaned_df.iterrows():
            item = SalesItem(
                report_id=report.id,
                product_name=row.get("product_name"),
                category=row.get("category") if pd.notna(row.get("category")) else "Uncategorized",
                qty_sold=_safe_int(row.get("qty_sold"), default=None),
                remaining_stock=_safe_int(row.get("remaining_stock"), default=None),
                unit_price=_safe_float(row.get("unit_price")),
                transaction_date=_safe_date(row.get("transaction_date")),
            )
            db.add(item)
        db.commit()
    except Exception as e:
        db.rollback()
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data: {str(e)}")

    # 5. Panggil Correlation Engine ch3coo
    try:
        corr_result = calculate_correlation(cleaned_df, target_lokasi, db)
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal menghitung korelasi: {str(e)}")

    # 6. Bentuk metrik health & correlation
    data_health = {
        "reliability_score": reliability_score,
        "status_color": "green" if reliability_score >= 70 else ("yellow" if reliability_score >= 40 else "red"),
        "warning_message": "; ".join(warnings) if warnings else None
    }
    correlation_metrics = {
        "keyword_overlap_score": corr_result["keyword_overlap_score"],
        "market_trend_growth": corr_result.get("market_trend_growth", "+0%"),
        "trend_reference_source": corr_result.get("trend_reference_source", "N/A")
    }

    # 7. Panggil LLM untuk blueprint inovasi
    try:
        innovations = generate_innovation_blueprint(
            cleaned_data=cleaned_df,
            data_health=data_health,
            correlation_metrics=correlation_metrics,
            target_lokasi=target_lokasi
        )
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # 8. Bersihkan file sementara
    os.unlink(tmp_path)

    # 9. Return response sesuai kontrak API
    return {
        "status": "success",
        "data_health": data_health,
        "correlation_metrics": correlation_metrics,
        "innovation_blueprint": innovations
    }