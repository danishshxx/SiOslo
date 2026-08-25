from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/simulate", tags=["Simulation"])

# --- SCHEMAS ---
class SimulateRequest(BaseModel):
    base_price: float
    cogs: float
    qty: int

class ScenarioResult(BaseModel):
    scenario_type: str
    sell_price: float
    cogs: float
    qty: int
    gross_margin_pct: float
    revenue: float
    est_profit: float

class SimulateResponse(BaseModel):
    scenarios: list[ScenarioResult]

# --- LOGIC ---
def calculate_scenario(name: str, price: float, cogs: float, qty: int) -> ScenarioResult:
    revenue = price * qty
    est_profit = (price - cogs) * qty
    gross_margin_pct = round(((price - cogs) / price) * 100, 2) if price > 0 else 0.0
    
    return ScenarioResult(
        scenario_type=name,
        sell_price=price,
        cogs=cogs,
        qty=qty,
        gross_margin_pct=gross_margin_pct,
        revenue=revenue,
        est_profit=est_profit
    )

@router.post("/", response_model=SimulateResponse)
async def get_pricing_simulation(req: SimulateRequest):
    """
    Menghasilkan 3 skenario harga (Conservative, Recommended, Premium) 
    berdasarkan harga dasar dan COGS.
    """
    # Rumus pengali skenario (bisa disesuaikan dengan standar bisnis lu)
    conservative_price = req.base_price * 0.90  # Turun 10%
    premium_price = req.base_price * 1.15       # Naik 15%

    return SimulateResponse(
        scenarios=[
            calculate_scenario("Conservative", conservative_price, req.cogs, req.qty),
            calculate_scenario("Recommended", req.base_price, req.cogs, req.qty),
            calculate_scenario("Premium", premium_price, req.cogs, req.qty),
        ]
    )