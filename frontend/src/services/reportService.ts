/**
 * reportService.ts — 报告 API 调用
 *
 * 调用后端 /api/v1/reports/* 端点
 */

const API_BASE = '/api/v1/reports';

export interface ReportListItem {
  report_id: string;
  title: string;
  province: string;
  subject_type: string;
  score: number;
  rank: number;
  plan_code: string;
  status: string;
  created_at: string;
  completed_at: string;
}

export interface ReportListResponse {
  success: boolean;
  total: number;
  reports: ReportListItem[];
}

export interface StudentProfile {
  province: string;
  subject_type: string;
  score: number;
  rank: number;
  total_candidates: number;
  strategy: string;
  generated_at: string;
}

export interface ExecutiveSummary {
  headline: string;
  key_finding: string;
  opportunities: string[];
  risks: string[];
  next_step: string;
}

export interface BucketSummary {
  rush: { count: number; description: string };
  stable: { count: number; description: string };
  safe: { count: number; description: string };
  total_recommended: number;
}

export interface RiskPreviewItem {
  risk_type: string;
  severity: string;
}

export interface KeyCandidatePreview {
  school_name: string;
  tier: string;
  school_level: string;
  score_gap: number;
}

export interface ReportSummary {
  student_profile: StudentProfile;
  executive_summary: ExecutiveSummary;
  score_positioning: Record<string, unknown>;
  bucket_summary: BucketSummary;
  risk_preview: RiskPreviewItem[];
  key_candidates_preview: KeyCandidatePreview[];
  download_permission: {
    can_download_pdf: boolean;
    required_plan: string | null;
  };
  plan_type: string;
}

export interface ReportSummaryResponse {
  success: boolean;
  report_id: string;
  plan_type: string;
  summary: ReportSummary;
}

export interface PdfDataResponse {
  success: boolean;
  report_id: string;
  pdf_type: string;
  report: Record<string, unknown>;
  branding: {
    product_name: string;
    theme: string;
    primary_color: string;
    accent_color: string;
    bg_color: string;
  };
  print_settings: {
    page_size: string;
    orientation: string;
    margin: string;
  };
}

export interface FullReportResponse {
  success: boolean;
  report_id: string;
  report: Record<string, unknown>;
  permission: {
    plan_type: string;
    locked_sections: string[];
  };
}

export interface PdfJobResponse {
  success: boolean;
  job_id?: string;
  status?: string;
  message?: string;
  download_url?: string;
  error_message?: string;
}

export async function fetchReportList(): Promise<ReportListResponse> {
  const res = await fetch(API_BASE);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/v1/reports/{report_id}/summary
 * 网页摘要报告页使用
 */
export async function fetchReportSummary(
  reportId: string,
): Promise<ReportSummaryResponse> {
  const res = await fetch(`${API_BASE}/${reportId}/summary`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/v1/reports/{report_id}/pdf-data
 * PDF 预览页使用
 */
export async function fetchPdfData(
  reportId: string,
): Promise<PdfDataResponse> {
  const res = await fetch(`${API_BASE}/${reportId}/pdf-data`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /api/v1/reports/{report_id}
 * 获取完整报告（含权限裁剪）
 */
export async function fetchFullReport(
  reportId: string,
): Promise<FullReportResponse> {
  const res = await fetch(`${API_BASE}/${reportId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * POST /api/v1/reports/{report_id}/pdf/jobs
 * 创建 PDF 生成任务
 */
export async function createPdfJob(
  reportId: string,
  pdfType: string = 'advanced',
): Promise<PdfJobResponse> {
  const res = await fetch(`${API_BASE}/${reportId}/pdf/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pdf_type: pdfType }),
  });
  if (!res.ok) {
    if (res.status === 403) throw new Error('您的版本不支持下载 PDF，请升级');
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * GET /api/v1/reports/pdf/jobs/{job_id}
 * 查询 PDF 任务状态
 */
export async function fetchPdfJobStatus(
  jobId: string,
): Promise<PdfJobResponse> {
  const res = await fetch(`/api/v1/reports/pdf/jobs/${jobId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
