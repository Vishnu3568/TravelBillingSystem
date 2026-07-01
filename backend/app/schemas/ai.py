from pydantic import BaseModel
from typing import List, Optional, Any, Dict

# AiAssistantRequest & AiAssistantResponse
class BillDataContext(BaseModel):
    billNumber: Optional[str] = None
    companyName: Optional[str] = None
    totalKm: Optional[float] = None
    totalHours: Optional[float] = None
    charges: Optional[List[Dict[str, Any]]] = None
    totalAmount: Optional[float] = None

class AggregatedDataContext(BaseModel):
    totalRevenue: Optional[float] = None
    topCompanies: Optional[List[Dict[str, Any]]] = None
    recentBills: Optional[List[Dict[str, Any]]] = None
    companyCount: Optional[int] = None
    vehicleCount: Optional[int] = None

class AiAssistantRequest(BaseModel):
    contextType: str  # BILL | GLOBAL
    billData: Optional[BillDataContext] = None
    aggregatedData: Optional[AggregatedDataContext] = None
    userQuery: str
    sessionId: str

class ActionData(BaseModel):
    type: str  # CREATE_BILL | DELETE_BILL
    data: Dict[str, Any]

class AiAssistantResponse(BaseModel):
    answer: str
    confidence: float
    references: Optional[List[str]] = None
    action: Optional[ActionData] = None

# AiBillResponse
class AiBillCharge(BaseModel):
    name: str
    amount: float

class AiBillResponse(BaseModel):
    dutySlipNo: Optional[str] = None
    billDate: Optional[str] = None
    companyName: Optional[str] = None
    vehicleNumber: Optional[str] = None
    vehicleType: Optional[str] = None
    totalKms: Optional[float] = None
    totalHours: Optional[float] = None
    dynamicCharges: Optional[List[AiBillCharge]] = None
    totalAmount: Optional[float] = None
    tripDate: Optional[str] = None
    contactPerson: Optional[str] = None
    bookedBy: Optional[str] = None
    warnings: Optional[List[str]] = None

# AiInsightResponse
class Insight(BaseModel):
    type: str
    message: str
    confidence: float

class AiInsightResponse(BaseModel):
    insights: List[Insight]

# AiSearchFilter
class AiSearchFilter(BaseModel):
    companyName: Optional[str] = None
    vehicleType: Optional[str] = None
    minAmount: Optional[float] = None
    maxAmount: Optional[float] = None
    minKm: Optional[float] = None
    maxKm: Optional[float] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    status: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None

# AiSuggestionRequest & AiSuggestionResponse
class CurrentBill(BaseModel):
    companyName: str
    vehicleType: str
    totalKm: Optional[float] = None
    totalHours: Optional[float] = None

class HistoricalPatterns(BaseModel):
    averageDriverBata: Optional[float] = None
    averageToll: Optional[float] = None
    averageParking: Optional[float] = None
    commonCharges: Optional[List[str]] = None
    recentSimilarBills: Optional[List[Dict[str, Any]]] = None

class AiSuggestionRequest(BaseModel):
    currentBill: CurrentBill
    historicalPatterns: HistoricalPatterns

class Suggestion(BaseModel):
    field: str
    suggestedValue: str
    reason: str
    confidence: float

class AiSuggestionResponse(BaseModel):
    suggestions: List[Suggestion]
