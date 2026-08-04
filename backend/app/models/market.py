import uuid
from sqlalchemy import Column, String, Integer, Float, Date, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class MarketTrend(Base):
    __tablename__ = "market_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(Text, nullable=False)
    volume = Column(Integer, default=0)
    source = Column(Text)
    date = Column(Date)

    # Tidak ada created_at, karena date sudah mewakili waktu tren
    # Jika ingin, bisa ditambahkan

class Demographic(Base):
    __tablename__ = "demographics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_area = Column(String(100), index=True)
    population_density = Column(Integer)
    dominant_age_group = Column(String(50))
    average_income = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FootTraffic(Base):
    __tablename__ = "foot_traffic"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_area = Column(String(100), index=True)
    time_period = Column(String(50))
    traffic_volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CompetitorPrice(Base):
    __tablename__ = "competitor_prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_name = Column(String(100), index=True)
    product_category = Column(String(100))
    average_price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())