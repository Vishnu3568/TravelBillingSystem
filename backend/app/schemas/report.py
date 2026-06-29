from pydantic import BaseModel

class ReportSummaryResponse(BaseModel):
    todayBillsCount: int
    todayRevenue: float
    monthlyBillsCount: int
    monthlyRevenue: float
    totalBillsCount: int
    totalCompanies: int
    totalVehicles: int

class TopEntityResponse(BaseModel):
    name: str
    revenue: float
