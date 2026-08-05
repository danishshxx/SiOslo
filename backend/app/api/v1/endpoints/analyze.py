import uuid
import os
import tempfile
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sales import SalesReport, SalesItem
from app.models.market import Demographic, CompetitorPrice   # ← tambahan
from app.services.csv_parser import parse_and_validate
from app.services.correlation_engine import compute_correlation   # ← langsung fungsi asli ch3coo
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

    # 3. Parser Jay
    parse_result = parse_and_validate(tmp_path)
    if parse_result["status"] == "error":
        os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=parse_result["data_health"]["warning_message"])

    cleaned_df = parse_result["cleaned_data"]
    health_raw = parse_result["data_health"]

    # 4. Simpan ke database
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
                category=row.get("category"),
                qty_sold=int(row.get("qty_sold", 0)),
                remaining_stock=int(row.get("remaining_stock", 0))
            )
            db.add(item)
        db.commit()
    except Exception as e:
        db.rollback()
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data: {str(e)}")

    # 5. Ambil data pasar dari database & konversi ke DataFrame
    try:
        demographics = db.query(Demographic).all()
        competitors = db.query(CompetitorPrice).all()

        # Konversi ke DataFrame (jika ada data)
        if demographics:
            demo_dicts = [{
                "category": d.dominant_age_group,   # misal kita pakai dominant_age_group sebagai kategori
                "segment_name": d.location_area,
                "keywords": d.dominant_age_group,   # seharusnya ada kolom keywords, tapi kita bisa pakai kombinasi
                # Untuk mengakali, kita buat field keywords dari gabungan yang ada
            } for d in demographics]
            # Buat kolom 'keywords' yang lebih kaya: gabungkan location_area + dominant_age_group
            for dd in demo_dicts:
                dd["keywords"] = f"{dd['segment_name']} {dd['category']}".lower()
            demographics_df = pd.DataFrame(demo_dicts)
        else:
            demographics_df = pd.DataFrame()

        if competitors:
            comp_dicts = [{
                "category": c.product_category,
                "product_name": c.competitor_name,
                "competitor_name": c.competitor_name,
                "price": float(c.average_price)
            } for c in competitors]
            competitors_df = pd.DataFrame(comp_dicts)
        else:
            competitors_df = pd.DataFrame()
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal mengambil data pasar: {str(e)}")

    # 6. Panggil correlation engine ch3coo
    try:
        corr_result = compute_correlation(cleaned_df, demographics_df, competitors_df)
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
    data_health = DataHealthMetric(
        reliability_score=health_raw["reliability_score"],
        status_color=health_raw["status_color"],
        warning_message=health_raw["warning_message"],
        score_breakdown=health_raw.get("score_breakdown"),
        issues=[DataHealthIssue(**iss) for iss in health_raw.get("issues", [])]
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