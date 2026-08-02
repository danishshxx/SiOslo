from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# ==========================================
# SCHEMAS UNTUK SALES ITEM (Anak / Detail)
# ==========================================
class SalesItemBase(BaseModel):
    product_name: str = Field(..., description="Nama produk")
    category: Optional[str] = Field(None, description="Kategori produk (opsional)")
    qty_sold: int = Field(0, description="Jumlah produk terjual")
    remaining_stock: int = Field(0, description="Sisa stok produk")

class SalesItemCreate(SalesItemBase):
    pass
    # Nanti pas bikin data, client nggak perlu kirim ID atau report_id, 
    # karena report_id akan disuntikkan otomatis dari backend.

class SalesItemResponse(SalesItemBase):
    id: UUID
    report_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SCHEMAS UNTUK SALES REPORT (Induk / Header)
# ==========================================
class SalesReportBase(BaseModel):
    filename: str = Field(..., description="Nama file CSV/laporan yang diupload")
    total_rows: int = Field(0, description="Total baris data dalam laporan")

class SalesReportCreate(SalesReportBase):
    pass

class SalesReportResponse(SalesReportBase):
    id: UUID
    uploaded_at: datetime
    
    # Fitur Keren: Kita bisa langsung nampilin list items di dalam response report-nya!
    items: List[SalesItemResponse] = [] 

    model_config = ConfigDict(from_attributes=True)