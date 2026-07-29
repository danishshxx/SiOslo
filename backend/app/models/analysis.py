import uuid
from sqlalchemy import Column, Text, Integer, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

# Tabel Pivot (Many-to-Many) antara Analyses dan MarketTrends
analysis_trend_refs = Table(
    "analysis_trend_refs",
    Base.metadata,
    Column("analysis_id", UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True),
    Column("trend_id", UUID(as_uuid=True), ForeignKey("market_trends.id", ondelete="CASCADE"), primary_key=True)
)

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("sales_reports.id", ondelete="CASCADE"), nullable=False)
    summary_text = Column(Text)
    correlation_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    report = relationship("SalesReport", back_populates="analyses")
    trends = relationship("MarketTrend", secondary=analysis_trend_refs, backref="analyses")
    innovations = relationship("Innovation", back_populates="analysis", cascade="all, delete-orphan")
    mentor_messages = relationship("MentorMessage", back_populates="analysis", cascade="all, delete-orphan")


class Innovation(Base):
    __tablename__ = "innovations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    innovation_name = Column(Text, nullable=False)
    probability_score = Column(Float)
    data_correlation = Column(Text)
    pricing_strategy = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    analysis = relationship("Analysis", back_populates="innovations")
    simulations = relationship("Simulation", back_populates="innovation", cascade="all, delete-orphan")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_id = Column(UUID(as_uuid=True), ForeignKey("innovations.id", ondelete="CASCADE"), nullable=False)
    scenario_input = Column(JSONB)
    scenario_result = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    innovation = relationship("Innovation", back_populates="simulations")


class MentorMessage(Base):
    __tablename__ = "mentor_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False) # 'user', 'assistant', 'system'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relasi
    analysis = relationship("Analysis", back_populates="mentor_messages")