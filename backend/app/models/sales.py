import uuid
from xml.dom.minidom import Text
from xmlrpc.client import DateTime
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class SalesReport(Base):
    __tablename__ = "sales_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(Text, nullable=False)
    total_rows = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relasi
    items = relationship("SalesItem", back_populates="report", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="report")
    
class SalesItem(Base):
    __tablename__ = "sales_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("sales_reports.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(Text, nullable=False)
    category = Column(Text)
    qty_sold = Column(Integer, default=0)
    remaining_stock = Column(Integer, default=0)

    # Relasi
    report = relationship("SalesReport", back_populates="items")