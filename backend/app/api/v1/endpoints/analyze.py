# File: app/api/v1/endpoints/analyze.py
import uuid
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sales import SalesReport, SalesItem
from app.services.csv_parser import parse_and_validate_csv
from app.services.correlation_engine import calculate_correlation
from app.services.llm_service import generate_innovation_blueprint
from app.schemas.analysis import AnalysisResponse

router = APIRouter(prefix="/analyze", tags=["Analysis"])

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
    except Exception as e:
        os.unlink(tmp_path)
        raise HTTPException(status_code=422, detail=f"CSV tidak valid: {str(e)}")

    # 4. Simpan data penjualan ke database
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
                product_name=row.get("nama_produk"),
                category=row.get("kategori"),
                qty_sold=int(row.get("terjual_bulan_ini", 0)),
                remaining_stock=int(row.get("sisa_stok", 0))
            )
            db.add(item)
        db.commit()
    except Exception as e:
        db.rollback()
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data: {str(e)}")

    # 5. Panggil Correlation Engine ch3coo
    try:
        corr_result = calculate_correlation(cleaned_df, target_lokasi)
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