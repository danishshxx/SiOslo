import datetime as dt
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

# -------------------- MarketTrend --------------------
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


# -------------------- Demographic --------------------
class DemographicBase(BaseModel):
    location_area: str
    population_density: int
    dominant_age_group: str
    average_income: float

class DemographicCreate(DemographicBase):
    pass

class DemographicResponse(DemographicBase):
    id: UUID
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)


# -------------------- FootTraffic --------------------
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


# -------------------- CompetitorPrice --------------------
class CompetitorPriceBase(BaseModel):
    competitor_name: str
    product_category: str
    average_price: float

class CompetitorPriceCreate(CompetitorPriceBase):
    pass

class CompetitorPriceResponse(CompetitorPriceBase):
    id: UUID
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)