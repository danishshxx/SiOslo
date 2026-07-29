import uuid
from sqlalchemy import Column, Text, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class MarketTrend(Base):
    __tablename__ = "market_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(Text, nullable=False)
    volume = Column(Integer, default=0)
    source = Column(Text)
    date = Column(Date)