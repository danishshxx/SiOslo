from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.sales import SalesReport, SalesItem
from app.services.csv_parser import parse_sales_csv

router = APIRouter(prefix="/sales", tags=["Sales"])

@router.post("/upload")
async def upload_sales_report(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # 1. Validasi ekstensi file
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Format tidak didukung. Harap upload file .csv")
        
    # 2. Baca isi file ke memory
    content = await file.read()
    
    # 3. Lempar ke Service Layer (Tugas Jay) buat diproses pakai Pandas
    parsed_data = parse_sales_csv(content, file.filename)
    
    try:
        # 4. Insert data induk ke tabel sales_reports
        new_report = SalesReport(
            filename=parsed_data["filename"],
            total_rows=parsed_data["total_rows"]
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # 5. Bulk insert data anak ke tabel sales_items (jauh lebih cepat dari nge-loop .add() satu per satu)
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
            "report_id": new_report.id,
            "total_rows_inserted": parsed_data["total_rows"]
        }
        
    except Exception as e:
        db.rollback() # Rollback kalau ada gagal insert supaya database gak kotor
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {str(e)}")

@router.get("/")
def get_all_reports(db: Session = Depends(get_db)):
    reports = db.query(SalesReport).all()
    return reports