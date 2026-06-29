from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, PasswordResetRequest
from app.schemas.user import UserRequest, UserResponse
from app.schemas.company import CompanyRequest, CompanyResponse
from app.schemas.vehicle import VehicleRequest, VehicleResponse
from app.schemas.bill import BillRequest, BillResponse, ChargeDTO
from app.schemas.dashboard import OwnerDashboardResponse, DashboardStats, RecentBill, UserActivity, RevenueTrend, DashboardStatsDTO, StatEntry
from app.schemas.report import ReportSummaryResponse, TopEntityResponse
from app.schemas.ai import (
    AiAssistantRequest, AiAssistantResponse, AiBillResponse, AiInsightResponse,
    AiSearchFilter, AiSuggestionRequest, AiSuggestionResponse, CurrentBill, HistoricalPatterns
)
from app.schemas.backup import BackupResponse
