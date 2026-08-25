from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

# -------------------- SalesItem --------------------
class SalesItemBase(BaseModel):
    product_name: str = Field(..., description="Nama produk")
    category: Optional[str] = Field(None, description="Kategori produk (opsional)")
    qty_sold: int = Field(0, ge=0, description="Jumlah produk terjual")
    remaining_stock: int = Field(0, ge=0, description="Sisa stok produk")

class SalesItemCreate(SalesItemBase):
    pass
    # report_id akan disuntikkan oleh backend dari relasi

class SalesItemResponse(SalesItemBase):
    id: UUID
    report_id: UUID

    model_config = ConfigDict(from_attributes=True)


# -------------------- SalesReport --------------------
class SalesReportBase(BaseModel):
    filename: str = Field(..., description="Nama file CSV/laporan yang diupload")
    total_rows: int = Field(0, ge=0, description="Total baris data dalam laporan")

class SalesReportCreate(SalesReportBase):
    pass

class SalesReportResponse(SalesReportBase):
    id: UUID
    uploaded_at: datetime
    items: List[SalesItemResponse] = []   # otomatis tampil saat pakai relationship

    model_config = ConfigDict(from_attributes=True)