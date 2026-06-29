// ========== Core Types for 择境 ZENPATH ==========

export interface User {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  province?: string;
  examType?: string;
  score?: number;
  rank?: number;
  createdAt: string;
}

export interface ExamScore {
  total: number;
  chinese?: number;
  math?: number;
  english?: number;
  physics?: number;
  history?: number;
  chemistry?: number;
  biology?: number;
  geography?: number;
  politics?: number;
}

export interface Preference {
  province: string;
  examType: '综合' | '物理' | '历史';
  score: ExamScore;
  rank: number;
  interests: string[];
  regions: string[];
  schoolTypes: string[];
  majorCategories: string[];
  budget?: number;
  priority: 'school' | 'major' | 'city';
}

export interface Major {
  id: string;
  name: string;
  category: string;
  description: string;
  avgSalary?: number;
  employmentRate?: number;
  hotness?: number;
}

export interface School {
  id: string;
  name: string;
  logo?: string;
  province: string;
  city: string;
  type: string;
  level: '985' | '211' | '双一流' | '普通';
  isPublic: boolean;
  tags: string[];
  description?: string;
  website?: string;
}

export interface VolunteerItem {
  id: string;
  schoolId: string;
  schoolName: string;
  schoolLogo?: string;
  majorId: string;
  majorName: string;
  majorCategory: string;
  tier: '冲刺' | '稳妥' | '保底' | '不推荐';
  probability: number;
  matchScore: number;
  expectedRank: number;
  reason: string;
  year: number;
  minRank?: number;
  avgRank?: number;
  maxRank?: number;
  minScore?: number;
  avgScore?: number;
  maxScore?: number;
  isRecommended: boolean;
  historicalData?: HistoricalDataPoint[];
  rag_summary?: string;
  recommendation_summary?: string;
  plan_count?: number;
  ai_explanation?: AIExplanation;
}

export interface AIExplanation {
  school_analysis?: string;
  major_analysis?: string;
  career_path?: string;
  risk_warning?: string;
  sources?: { source_name: string; source_url: string }[];
}

export interface HistoricalDataPoint {
  year: number;
  minRank: number;
  avgRank: number;
  maxRank: number;
  minScore: number;
  avgScore: number;
  maxScore: number;
  enrollmentCount: number;
}

export interface Recommendation {
  id: string;
  userId: string;
  score: ExamScore;
  rank: number;
  province: string;
  createdAt: string;
  rush: VolunteerItem[];
  stable: VolunteerItem[];
  safe: VolunteerItem[];
  notRecommended: VolunteerItem[];
  summary: string;
  matchRate: number;
  totalSchools: number;
  totalMajors: number;
}

export interface Order {
  id: string;
  userId: string;
  plan: PricingPlan;
  amount: number;
  status: 'pending' | 'paid' | 'cancelled' | 'refunded';
  createdAt: string;
  paidAt?: string;
}

export type PricingPlan = 'free' | 'basic' | 'advanced' | 'premium';

export interface PricingTier {
  id: PricingPlan;
  name: string;
  price: number;
  originalPrice?: number;
  billingCycle?: string;
  description: string;
  features: string[];
  isPopular?: boolean;
  badge?: string;
}

export interface ChatSource {
  title: string;
  source_url: string;
  doc_type: string;
  school_name?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: 'text' | 'recommendation' | 'chart';
  metadata?: Record<string, unknown>;
  sources?: ChatSource[];
  answerable?: boolean;
  intent?: string;
  structured?: Record<string, unknown>;
}

export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  message_count?: number;
  messages: ChatMessage[];
  context?: Preference;
  createdAt: string;
  updatedAt: string;
}

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

export interface NavLink {
  label: string;
  href: string;
  icon?: string;
}

export interface FeatureItem {
  icon: string;
  title: string;
  description: string;
}

export interface StepItem {
  icon: string;
  title: string;
  description: string;
  step: number;
}

export interface StatsData {
  schools: number;
  majors: number;
  provinces: number;
  years: number;
}

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// ========== Jiangsu Recommendation Types ==========

export interface JiangsuGroupItem {
  school_code: number;
  school_name: string;
  school_tier: string;
  major_group_code: number;
  major_group_full_name: string;
  elective_requirement: string;
  bucket: '冲' | '稳' | '保' | '垫';
  latest_min_score: number;
  latest_min_rank: number;
  user_score: number;
  user_rank: number;
  rank_delta: number;
  rank_delta_ratio: number;
  years_available: number;
  rank_avg: number | null;
  rank_best: number | null;
  rank_worst: number | null;
  rank_volatility: number | null;
  rank_change_latest_vs_prev: number | null;
  score_avg: number | null;
  score_best: number | null;
  score_worst: number | null;
  subject_match_status: 'matched' | 'not_matched' | 'need_review';
  subject_match_note: string;
  matched_majors: JiangsuMajorMatch[];
  majors: JiangsuGroupMajor[];
  group_major_status: 'complete' | 'partial' | 'missing';
  group_plan_count: number;
  risk_tags: string[];
  risk_level: 'low' | 'medium' | 'high';
  reason: string;
  source_url: string;
  total_score: number;
  score_breakdown: {
    rank_fit: number;
    trend_stability: number;
    subject_match: number;
    major_match: number;
    city_match: number;
    data_confidence: number;
  };
  rag_evidence?: {
    school_profile_available: boolean;
    admission_policy_available: boolean;
    source_count: number;
    sources: Array<{ title: string; doc_type: string; source_url: string }>;
  };
}

export interface JiangsuGroupMajor {
  major_name: string;
  plan_count: number;
  major_name_clean: string;
}

export interface JiangsuMajorMatch {
  major_name: string;
  match_score: number;
  match_type: string;
  reason: string;
}

export interface JiangsuRecommendResponse {
  success: boolean;
  province: string;
  subject_type: string;
  score: number;
  user_rank: number;
  estimated_rank_from_score: number | null;
  rank_source: string;
  rank_warning: string | null;
  recommendations: {
    冲: JiangsuGroupItem[];
    稳: JiangsuGroupItem[];
    保: JiangsuGroupItem[];
    垫: JiangsuGroupItem[];
  };
  summary: {
    total_candidates: number;
    冲: number;
    稳: number;
    保: number;
    垫: number;
    candidate_pool: number;
    filtered_by_elective: number;
    filtered_by_bucket: number;
    deduplicated: number;
  };
  warnings: string[];
  data_note: string;
  debug?: Record<string, unknown>;
}

// ========== RAG Summary Types ==========

export interface RagDataAvailability {
  total_unique_schools: number;
  schools_with_profile: number;
  schools_with_policy: number;
  schools_missing: number;
  unique_source_urls: number;
}

export interface RagSummary {
  data_availability: RagDataAvailability;
  schools_with_profiles: string[];
  schools_with_policies: string[];
  missing_schools: string[];
  source_citations: string[];
  disclaimer: string;
}

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
