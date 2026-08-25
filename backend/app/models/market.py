import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, Integer, Date, String, Float, DateTime, CheckConstraint, text
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
    __tablename__ = "demographics"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default=text("gen_random_uuid()"))
    category = Column(Text, nullable=False, index=True)
    segment_name = Column(Text, nullable=False)
    keywords = Column(Text, nullable=False)
    age_group = Column(String(50))
    source = Column(Text)
    recorded_at = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))

class FootTraffic(Base):
    """Model untuk menyimpan data tingkat keramaian/lalu lalang di suatu area.
    Belum dipakai fitur manapun saat ini -- disiapkan untuk roadmap Hyper-Local."""
    __tablename__ = "foot_traffic"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_area = Column(String(100), index=True)
    time_period = Column(String(50), comment="Misal: Pagi, Siang, Sore, Malam")
    traffic_volume = Column(Integer, comment="Estimasi jumlah orang lewat per jam")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompetitorPrice(Base):
    """Model untuk menyimpan benchmarking harga kompetitor per kategori & nama produk
    (dipakai correlation_engine.py untuk price_competitiveness_score). Skema mengikuti
    ch3coo, selaras dengan tabel demographics di atas."""
    __tablename__ = "competitor_prices"

    id = Column(UUID(as_uuid=True), primary_key=True,
                server_default=text("gen_random_uuid()"))
    category = Column(Text, nullable=False, index=True)
    product_name = Column(Text, nullable=False)
    competitor_name = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    recorded_at = Column(Date, nullable=False, server_default=text("CURRENT_DATE"))

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_competitor_prices_price_positive"),
    )