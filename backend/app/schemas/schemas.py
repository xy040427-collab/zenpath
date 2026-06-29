from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================
# Common
# ============================================================

class ApiResponse(BaseModel):
    success: bool = True
    code: str = "OK"
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None


# ============================================================
# Session
# ============================================================

class SessionCreate(BaseModel):
    source: str = "web"
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    session_token: str
    expires_at: str


# ============================================================
# Application / Exam / Preferences / Profile
# ============================================================

class ApplicationCreate(BaseModel):
    session_id: str

class ExamInfo(BaseModel):
    province: str
    year: int = 2026
    subject_type: str  # physics, history
    score: int = Field(..., ge=0, le=750)
    rank: int = Field(..., ge=1)
    gender: Optional[str] = None
    single_subject_scores: Optional[Dict[str, float]] = None
    target_batch: str = "普通本科批"


class Preferences(BaseModel):
    priority: str = "balanced"
    risk_preference: str = "balanced"
    preferred_cities: List[str] = []
    accept_private_university: bool = False
    accept_sino_foreign: bool = False
    accept_high_tuition: bool = False
    max_tuition_per_year: int = 12000
    school_vs_major: str = "balanced"
    accept_major_adjustment: bool = True
    preferred_major_categories: Optional[List[str]] = None


class ProfileInfo(BaseModel):
    gender: Optional[str] = None
    interests: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    career_goals: Optional[List[str]] = None
    family_budget: Optional[int] = None


# ============================================================
# Pricing
# ============================================================

class PricingPlanResponse(BaseModel):
    plan_code: str
    name: str
    price: float
    original_price: Optional[float] = None
    features: List[str] = []
    is_popular: bool = False


class PricingPlansResponse(BaseModel):
    plans: List[PricingPlanResponse]


# ============================================================
# Recommendations
# ============================================================

class PreviewRequest(BaseModel):
    application_id: str


class PreviewResponse(BaseModel):
    preview_id: str
    summary: Dict[str, Any]
    sample_recommendations: List[Dict[str, Any]]
    upgrade_suggestion: Dict[str, Any]


class FullRecommendationRequest(BaseModel):
    application_id: str
    plan_code: str


# ============================================================
# Orders
# ============================================================

class OrderCreate(BaseModel):
    application_id: str
    plan_code: str
    coupon_code: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    order_no: str
    plan_code: str
    original_amount: float
    discount_amount: float = 0
    pay_amount: float
    status: str


# ============================================================
# Reports
# ============================================================

class ReportGenerate(BaseModel):
    application_id: str
    recommendation_result_id: str
    plan_code: str


class ReportCreate(BaseModel):
    """POST /api/reports — 创建报告（文档 7.1）"""
    recommendation_id: str
    report_level: str = "advanced"


class PdfJobCreate(BaseModel):
    """POST /api/reports/{id}/pdf/jobs — 创建 PDF 任务（文档 7.5）"""
    pdf_type: str = "advanced"


class ReportJobResponse(BaseModel):
    report_job_id: str
    status: str


# ============================================================
# AI Chat
# ============================================================

class ConversationCreate(BaseModel):
    report_id: str
    title: str = "新对话"


class MessageCreate(BaseModel):
    message: str


class Citation(BaseModel):
    type: str = "recommendation"
    id: str
    title: str


class AiAnswer(BaseModel):
    answer: str
    citations: List[Citation] = []
    risk_notice: str = "该回答仅供参考，最终以官方填报系统和高校招生章程为准。"


# ============================================================
# Admission Lines Query
# ============================================================

class AdmissionLineQuery(BaseModel):
    province: Optional[str] = None
    year: Optional[int] = None
    university_id: Optional[str] = None
    subject_type: Optional[str] = None
    page: int = 1
    page_size: int = 20
