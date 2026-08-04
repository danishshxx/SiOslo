from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.market import Demographic, FootTraffic, CompetitorPrice, MarketTrend
from app.schemas.market import (
    DemographicCreate, DemographicResponse,
    FootTrafficCreate, FootTrafficResponse,
    CompetitorPriceCreate, CompetitorPriceResponse,
    MarketTrendCreate, MarketTrendResponse
)

router = APIRouter(prefix="/market", tags=["Market"])

# --- Demographic ---
@router.post("/demographics", response_model=DemographicResponse, status_code=status.HTTP_201_CREATED)
def create_demographic(data: DemographicCreate, db: Session = Depends(get_db)):
    new_demo = Demographic(**data.model_dump())
    db.add(new_demo)
    db.commit()
    db.refresh(new_demo)
    return new_demo

@router.get("/demographics", response_model=List[DemographicResponse])
def get_demographics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Demographic).offset(skip).limit(limit).all()

# --- Foot Traffic ---
@router.post("/foot-traffic", response_model=FootTrafficResponse, status_code=status.HTTP_201_CREATED)
def create_foot_traffic(data: FootTrafficCreate, db: Session = Depends(get_db)):
    new_traffic = FootTraffic(**data.model_dump())
    db.add(new_traffic)
    db.commit()
    db.refresh(new_traffic)
    return new_traffic

@router.get("/foot-traffic", response_model=List[FootTrafficResponse])
def get_foot_traffic(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(FootTraffic).offset(skip).limit(limit).all()

# --- Competitor Price ---
@router.post("/competitor-prices", response_model=CompetitorPriceResponse, status_code=status.HTTP_201_CREATED)
def create_competitor_price(data: CompetitorPriceCreate, db: Session = Depends(get_db)):
    new_price = CompetitorPrice(**data.model_dump())
    db.add(new_price)
    db.commit()
    db.refresh(new_price)
    return new_price

@router.get("/competitor-prices", response_model=List[CompetitorPriceResponse])
def get_competitor_prices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(CompetitorPrice).offset(skip).limit(limit).all()

# --- Market Trend ---
@router.post("/trends", response_model=MarketTrendResponse, status_code=status.HTTP_201_CREATED)
def create_market_trend(data: MarketTrendCreate, db: Session = Depends(get_db)):
    new_trend = MarketTrend(**data.model_dump())
    db.add(new_trend)
    db.commit()
    db.refresh(new_trend)
    return new_trend

@router.get("/trends", response_model=List[MarketTrendResponse])
def get_market_trends(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(MarketTrend).offset(skip).limit(limit).all()