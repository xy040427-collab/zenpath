import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def gen_id():
    return str(uuid.uuid4().hex[:24])


def gen_order_no():
    from datetime import datetime
    return f"GKV{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(24), primary_key=True, default=gen_id)
    session_token = Column(String(64), unique=True, nullable=False)
    source = Column(String(32), default="web")
    utm_source = Column(String(64), nullable=True)
    utm_campaign = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    applications = relationship("Application", back_populates="session")


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(24), primary_key=True, default=gen_id)
    session_id = Column(String(24), ForeignKey("sessions.id"), nullable=False)
    status = Column(String(16), default="draft")  # draft, completed, paid

    # Exam info
    province = Column(String(16), nullable=True)
    year = Column(Integer, nullable=True)
    subject_type = Column(String(16), nullable=True)  # physics, history
    score = Column(Integer, nullable=True)
    rank = Column(Integer, nullable=True)
    gender = Column(String(4), nullable=True)
    single_subject_scores = Column(JSON, nullable=True)
    target_batch = Column(String(32), default="普通本科批")

    # Preferences
    priority = Column(String(16), nullable=True)
    risk_preference = Column(String(16), nullable=True)
    preferred_cities = Column(JSON, nullable=True)
    accept_private_university = Column(Boolean, default=False)
    accept_sino_foreign = Column(Boolean, default=False)
    accept_high_tuition = Column(Boolean, default=False)
    max_tuition_per_year = Column(Integer, default=12000)
    school_vs_major = Column(String(16), default="balanced")
    accept_major_adjustment = Column(Boolean, default=True)
    preferred_major_categories = Column(JSON, nullable=True)

    # Profile
    interests = Column(JSON, nullable=True)
    strengths = Column(JSON, nullable=True)
    career_goals = Column(JSON, nullable=True)
    family_budget = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("Session", back_populates="applications")
    recommendations = relationship("RecommendationResult", back_populates="application", uselist=False)
    orders = relationship("Order", back_populates="application")
    reports = relationship("Report", back_populates="application", uselist=False)


# ═══════════════════════════════════════════════
# SQL-RAG 推荐模块新表
# ═══════════════════════════════════════════════

class ScoreRankTable(Base):
    """一分一段表"""
    __tablename__ = "score_rank_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    province = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    subject_type = Column(String(50), default='全体')  # 全体/选考物理/选考化学/...
    score = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    same_score_count = Column(Integer, nullable=True)
    segment_count = Column(Integer, nullable=True)
    cumulative_count = Column(Integer, nullable=True)
    rank_start = Column(Integer, nullable=True)
    rank_end = Column(Integer, nullable=True)
    data_source = Column(String(20), default='official')
    created_at = Column(DateTime, default=datetime.utcnow)


class SubjectRequirement(Base):
    """选科要求表"""
    __tablename__ = "subject_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school_code = Column(String(50), nullable=True, index=True)
    school_name = Column(String(200), nullable=True)
    major_code = Column(String(50), nullable=True)
    major_name = Column(String(200), nullable=True)
    province = Column(String(50), nullable=True, index=True)
    year = Column(Integer, nullable=True)
    required_subjects = Column(Text, nullable=True)
    requirement_type = Column(String(100), nullable=True)
    data_source = Column(String(20), default='mock')
    created_at = Column(DateTime, default=datetime.utcnow)


class RagChunk(Base):
    """RAG 文本知识表"""
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(100), unique=True, nullable=True)
    doc_type = Column(String(100), nullable=False, index=True)  # 学校介绍/专业介绍/招生章程/就业报告/城市资料
    school_code = Column(String(50), nullable=True, index=True)
    school_name = Column(String(200), nullable=True, index=True)
    major_code = Column(String(50), nullable=True)
    major_name = Column(String(200), nullable=True)
    province = Column(String(50), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    title = Column(String(500), nullable=True)
    section = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    data_source = Column(String(20), default='mock')
    created_at = Column(DateTime, default=datetime.utcnow)


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id = Column(String(24), primary_key=True, default=gen_id)
    application_id = Column(String(24), ForeignKey("applications.id"), nullable=False, unique=True)
    strategy_summary = Column(Text, nullable=True)
    summary_data = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    not_recommended = Column(JSON, nullable=True)
    tier_distribution = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="recommendations")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(24), primary_key=True, default=gen_id)
    order_no = Column(String(32), unique=True, nullable=False, default=gen_order_no)
    application_id = Column(String(24), ForeignKey("applications.id"), nullable=False)
    plan_code = Column(String(16), nullable=False)  # basic, advanced, premium
    original_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    pay_amount = Column(Float, nullable=False)
    coupon_code = Column(String(32), nullable=True)
    status = Column(String(16), default="pending")  # pending, paid, refunded, cancelled
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="orders")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(24), primary_key=True, default=gen_id)
    application_id = Column(String(24), ForeignKey("applications.id"), nullable=False)
    recommendation_result_id = Column(String(24), nullable=False)
    plan_code = Column(String(16), nullable=False)
    status = Column(String(16), default="pending")  # pending, generating, completed, failed
    # ── 新增：文档要求的字段 ──
    user_id = Column(String(24), nullable=True)
    province = Column(String(16), nullable=True)
    subject_type = Column(String(16), nullable=True)
    score = Column(Integer, nullable=True)
    rank = Column(Integer, nullable=True)
    title = Column(String(128), nullable=True)
    summary = Column(Text, nullable=True)
    report_json = Column(JSON, nullable=True)  # 文档指定的统一 Report JSON
    report_data = Column(JSON, nullable=True)  # 保留兼容旧字段
    pdf_path = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    application = relationship("Application", back_populates="reports")
    pdf_jobs = relationship("ReportPdfJob", back_populates="report")
    files = relationship("ReportFile", back_populates="report")


class ReportPdfJob(Base):
    __tablename__ = "report_pdf_jobs"

    id = Column(String(24), primary_key=True, default=gen_id)
    report_id = Column(String(24), ForeignKey("reports.id"), nullable=False)
    user_id = Column(String(24), nullable=True)
    plan_type = Column(String(16), nullable=False)
    status = Column(String(16), default="pending")
    file_path = Column(String(256), nullable=True)
    file_url = Column(String(256), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    report = relationship("Report", back_populates="pdf_jobs")


class ReportFile(Base):
    __tablename__ = "report_files"

    id = Column(String(24), primary_key=True, default=gen_id)
    report_id = Column(String(24), ForeignKey("reports.id"), nullable=False)
    user_id = Column(String(24), nullable=True)
    file_type = Column(String(16), nullable=False)
    file_name = Column(String(128), nullable=False)
    file_path = Column(String(256), nullable=False)
    file_url = Column(String(256), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    report = relationship("Report", back_populates="files")


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(String(24), primary_key=True, default=gen_id)
    report_id = Column(String(24), nullable=False)
    title = Column(String(128), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("AIChatMessage", back_populates="conversation")


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id = Column(String(24), primary_key=True, default=gen_id)
    conversation_id = Column(String(24), ForeignKey("ai_conversations.id"), nullable=False)
    role = Column(String(16), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    prompt_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("AIConversation", back_populates="messages")


class AdmissionLine(Base):
    __tablename__ = "admission_lines"

    id = Column(String(24), primary_key=True, default=gen_id)
    year = Column(Integer, nullable=False)
    province = Column(String(16), nullable=False)
    subject_type = Column(String(16), nullable=False)
    university_id = Column(String(24), nullable=True)
    university_name = Column(String(64), nullable=False)
    major_group_code = Column(String(16), nullable=True)
    major_group_name = Column(String(64), nullable=True)
    batch = Column(String(32), default="普通本科批")
    min_score = Column(Integer, nullable=False)
    min_rank = Column(Integer, nullable=False)
    plan_count = Column(Integer, default=0)
    source_id = Column(String(24), nullable=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PricingPlan(Base):
    __tablename__ = "pricing_plans"

    id = Column(String(24), primary_key=True, default=gen_id)
    plan_code = Column(String(16), unique=True, nullable=False)
    name = Column(String(32), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    features = Column(JSON, nullable=True)
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════
# NEW: School model — all 863 universities
# ═══════════════════════════════════════════════

class School(Base):
    __tablename__ = "schools"

    id = Column(String(24), primary_key=True, default=gen_id)
    slug = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False, index=True)
    province = Column(String(32), nullable=False, index=True)
    city = Column(String(32), nullable=False)
    type = Column(String(16), nullable=False)  # 综合/理工/师范/医药/农林/政法/财经/艺术/体育
    level = Column(String(16), nullable=False, index=True)  # 985/211/双一流/普通
    ranking = Column(Integer, nullable=False, index=True)
    is_public = Column(Boolean, default=True)
    tags = Column(JSON, nullable=True)  # ["双一流", "C9联盟"]
    description = Column(Text, nullable=True)
    website = Column(String(256), nullable=True)
    logo_slug = Column(String(128), nullable=True)  # urongda slug for logo display
    created_at = Column(DateTime, default=datetime.utcnow)
