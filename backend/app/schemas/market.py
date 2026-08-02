from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID

# ==========================================
# Schemas untuk MarketTrend
# ==========================================
class MarketTrendBase(BaseModel):
    keyword: str
    volume: int = 0
    source: Optional[str] = None
    date: Optional[date] = None

class MarketTrendCreate(MarketTrendBase):
    pass

class MarketTrendResponse(MarketTrendBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas untuk Demographic
# ==========================================
class DemographicBase(BaseModel):
    location_area: str
    population_density: int
    dominant_age_group: str
    average_income: float

class DemographicCreate(DemographicBase):
    pass

class DemographicResponse(DemographicBase):
    id: UUID
    created_at: datetime
    
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
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas untuk CompetitorPrice
# ==========================================
class CompetitorPriceBase(BaseModel):
    competitor_name: str
    product_category: str
    average_price: float

class CompetitorPriceCreate(CompetitorPriceBase):
    pass

class CompetitorPriceResponse(CompetitorPriceBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)