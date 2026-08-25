from __future__ import annotations
import datetime as dt
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

# ==========================================
# Schemas untuk MarketTrend
# ==========================================
class MarketTrendBase(BaseModel):
    keyword: str
    volume: int = 0
    source: Optional[str] = None
    date: Optional[dt.date] = None

class MarketTrendCreate(MarketTrendBase):
    pass

class MarketTrendResponse(MarketTrendBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas untuk Demographic
# ==========================================
class DemographicBase(BaseModel):
    category: str
    segment_name: str
    keywords: str
    age_group: Optional[str] = None
    source: Optional[str] = None

class DemographicCreate(DemographicBase):
    pass

class DemographicResponse(DemographicBase):
    id: UUID
    recorded_at: dt.date

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas untuk FootTraffic
# ==========================================
class FootTrafficBase(BaseModel):
    location_area: str
    time_period: str
    traffic_volume: int

class FootTrafficCreate(FootTrafficBase):
    pass

class FootTrafficResponse(FootTrafficBase):
    id: UUID
    created_at: dt.datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas untuk CompetitorPrice
# ==========================================
class CompetitorPriceBase(BaseModel):
    category: str
    product_name: str
    competitor_name: str
    price: float

class CompetitorPriceCreate(CompetitorPriceBase):
    pass

class CompetitorPriceResponse(CompetitorPriceBase):
    id: UUID
    recorded_at: dt.date

    model_config = ConfigDict(from_attributes=True)