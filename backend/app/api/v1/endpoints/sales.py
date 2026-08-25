from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db               # dari core, bukan api.deps
from app.models.sales import SalesReport, SalesItem
from app.services.csv_parser import parse_sales_csv  # placeholder

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("/upload")
def upload_sales_report(              # bukan async def
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validasi ekstensi file
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Format tidak didukung. Harap upload file .csv")

    # 2. Baca isi file (sinkron)
    try:
        content = file.file.read()      # baca langsung, bukan await
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")

    # 3. Parsing CSV via service layer (Jay)
    try:
        parsed_data = parse_sales_csv(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV tidak valid: {str(e)}")

    # 4. Simpan ke database
    try:
        new_report = SalesReport(
            filename=parsed_data["filename"],
            total_rows=parsed_data["total_rows"]
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        items_to_insert = [
            SalesItem(
                report_id=new_report.id,
                product_name=item["product_name"],
                category=item.get("category", "Uncategorized"),
                qty_sold=item["qty_sold"],
                remaining_stock=item["remaining_stock"]
            )
            for item in parsed_data["items"]
        ]

        db.bulk_save_objects(items_to_insert)
        db.commit()

        return {
            "message": "File CSV berhasil diproses dan disimpan ke database!",
            "report_id": str(new_report.id),
            "total_rows_inserted": parsed_data["total_rows"]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {str(e)}")

@router.get("/")
def get_all_reports(db: Session = Depends(get_db)):
    return db.query(SalesReport).all()