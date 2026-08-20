from app.services.csv_parser import parse_and_validate_csv
from app.services.correlation_engine import calculate_correlation
import uuid
import os
import tempfile
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sales import SalesReport, SalesItem
from app.models.market import Demographic, CompetitorPrice
from app.services.csv_parser import parse_and_validate
from app.services.correlation_engine import compute_correlation
from app.services.llm_service import generate_innovation_blueprint
from app.schemas.analysis import (
    AnalysisResponse,
    DataHealthMetric,
    DataHealthIssue,
    CorrelationMetric,
    PerProductScore,   # ← tambahan
    InnovationBlueprintItem,
)

router = APIRouter(prefix="/analyze")



def _safe_int(value, default=0):
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
    # 1. session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    # 2. Simpan CSV sementara
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
        raise HTTPException(status_code=500, detail=f"Error tak terduga: {str(e)}")

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
        db.flush()

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

    # 5. Ambil data pasar dari database & konversi ke DataFrame
    try:
        corr_result = calculate_correlation(cleaned_df, target_lokasi, db)
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal menghitung korelasi: {str(e)}")

    # 7. Ekstrak metrik ringkasan
    if corr_result["status"] == "success":
        kw_data = corr_result["correlation_data"]["keyword_overlap"]
        price_data = corr_result["correlation_data"]["price_competitiveness"]

        # Rata-rata keyword overlap
        scores = [p["keyword_overlap_score"] for p in kw_data.get("per_product", [])]
        avg_kw_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        # Gabungkan detail per produk
        # Gabungkan detail per produk
        per_product_details = []
        for kw, pr in zip(kw_data.get("per_product", []), price_data.get("per_product", [])):
            per_product_details.append(PerProductScore(
                product_name=kw["product_name"],
                category=kw.get("category"),
                keyword_overlap_score=kw["keyword_overlap_score"],
                matched_keywords=kw.get("matched_keywords", []),
                matched_segment=kw.get("matched_segment"),
                price_competitiveness_score=pr.get("price_competitiveness_score"),
                user_price=pr.get("user_price"),
                avg_competitor_price=pr.get("avg_competitor_price")
            ))

        # Jika tidak ada detail, set None agar validasi Pydantic lolos
        if not per_product_details:
            per_product_details = None
    else:
        avg_kw_score = 0.0
        per_product_details = None

    # Sementara market_trend_growth kita isi placeholder, bisa dari foot_traffic nanti
    market_trend_growth = "+0%"
    trend_reference_source = "static_snapshot"

    # 8. Bangun response data_health
    status_color = "green" if reliability_score >= 80 else "yellow" if reliability_score >= 50 else "red"

    data_health = DataHealthMetric(
        reliability_score=reliability_score,
        status_color=status_color,
        warning_message=warnings[0] if warnings else None,
        score_breakdown=None,
        issues=None
    )

    correlation_metrics = CorrelationMetric(
        keyword_overlap_score=avg_kw_score,
        market_trend_growth=market_trend_growth,
        trend_reference_source=trend_reference_source,
        per_product_details=per_product_details
    )

    # 9. LLM (masih placeholder)
    try:
        innovations = generate_innovation_blueprint(
            cleaned_data=cleaned_df,
            data_health=data_health.model_dump(),
            correlation_metrics=correlation_metrics.model_dump(),
            target_lokasi=target_lokasi
        )
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    os.unlink(tmp_path)

    return {
        "status": "success",
        "data_health": data_health,
        "correlation_metrics": correlation_metrics,
        "innovation_blueprint": innovations
    }