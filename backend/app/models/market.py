import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, Integer, Date, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class MarketTrend(Base):
    __tablename__ = "market_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(Text, nullable=False)
    volume = Column(Integer, default=0)
    source = Column(Text)
    date = Column(Date)

class Demographic(Base):
    """Model untuk menyimpan data demografi suatu area (target pasar)"""
    __tablename__ = "demographics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_area = Column(String(100), index=True)
    population_density = Column(Integer, comment="Kepadatan per km persegi")
    dominant_age_group = Column(String(50))
    average_income = Column(Float, comment="Rata-rata pendapatan (IDR)")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class FootTraffic(Base):
    """Model untuk menyimpan data tingkat keramaian/lalu lalang di suatu area"""
    __tablename__ = "foot_traffic"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_area = Column(String(100), index=True)
    time_period = Column(String(50), comment="Misal: Pagi, Siang, Sore, Malam")
    traffic_volume = Column(Integer, comment="Estimasi jumlah orang lewat per jam")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompetitorPrice(Base):
    """Model untuk menyimpan benchmarking harga dari kompetitor F&B/Retail sekitar"""
    __tablename__ = "competitor_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_name = Column(String(100), index=True)
    product_category = Column(String(100))
    average_price = Column(Float, comment="Harga rata-rata produk kompetitor (IDR)")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))