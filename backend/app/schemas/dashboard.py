from pydantic import BaseModel
from typing import List, Optional

class DashboardStats(BaseModel):
    todayBillsCount: int
    todayRevenue: float
    monthlyRevenue: float
    pendingPayments: float
    totalCompanies: int
    totalVehicles: int

class RevenueTrend(BaseModel):
    month: str
    revenue: float

class RecentBill(BaseModel):
    id: int
    billNumber: str
    companyName: Optional[str] = None
    vehicleRegistrationNumber: Optional[str] = None
    amount: float
    paidAmount: float
    pendingAmount: float
    status: str
    billDate: Optional[str] = None

class UserActivity(BaseModel):
    id: int
    action: str
    performedBy: str
    actionTime: Optional[str] = None

class OwnerDashboardResponse(BaseModel):
    stats: DashboardStats
    revenueTrend: List[RevenueTrend]
    recentBills: List[RecentBill]
    recentUsersActivity: List[UserActivity]

class StatEntry(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    count: Optional[int] = None

class DashboardStatsDTO(BaseModel):
    totalRevenue: Optional[float] = None
    billCount: Optional[int] = None
    companyStats: List[StatEntry]
    vehicleStats: List[StatEntry]
    monthlyRevenue: List[StatEntry]
    chargeStats: List[StatEntry]
