import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Download, Share2, ShieldAlert, Flag, TrendingUp,
  Lock, Sparkles, Loader2, FileText, GraduationCap,
  Calendar, ChevronRight, BarChart3, MapPin, Clock,
} from 'lucide-react';
import {
  fetchReportSummary, createPdfJob, fetchPdfJobStatus, fetchReportList,
} from '../services/reportService';
import type {
  ReportSummaryResponse, ReportSummary, StudentProfile,
  ExecutiveSummary, BucketSummary, RiskPreviewItem, KeyCandidatePreview,
  ReportListItem,
} from '../services/reportService';
import LoadingSpinner from '../components/ui/LoadingSpinner';

// ─── Types ───────────────────────────────────────────────────────

interface PdfJobState {
  status: 'idle' | 'creating' | 'polling' | 'ready' | 'error';
  jobId?: string;
  downloadUrl?: string;
  error?: string;
}

// ─── Styles map ──────────────────────────────────────────────────

const TIER_STYLES: Record<string, string> = {
  '冲刺': 'bg-blue-100 text-blue-800',
  '稳妥': 'bg-emerald-100 text-emerald-800',
  '保底': 'bg-amber-100 text-amber-800',
};

const SEVERITY_STYLES: Record<string, string> = {
  '高': 'bg-red-100 text-red-800',
  '中': 'bg-amber-100 text-amber-800',
  '低': 'bg-gray-100 text-gray-600',
};

function getTierStyle(tier: string): string {
  return TIER_STYLES[tier] || 'bg-gray-100 text-gray-600';
}

function getSeverityStyle(severity: string): string {
  return SEVERITY_STYLES[severity] || 'bg-gray-100 text-gray-600';
}

// ─── Stagger animation variants ──────────────────────────────────

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
};

// ─── Plan type badge ─────────────────────────────────────────────

function PlanBadge({ planType }: { planType: string }) {
  const labelMap: Record<string, string> = {
    free: '免费版',
    basic: '基础版',
    advanced: '进阶版',
    premium: '尊享版',
  };
  return (
    <span className="inline-block px-3 py-1 rounded-full bg-beige-100 text-beige-700 font-sans text-xs font-medium">
      {labelMap[planType] || planType}
    </span>
  );
}

// ─── Main Component ──────────────────────────────────────────────

export default function Report() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ReportSummaryResponse | null>(null);
  const [pdfJob, setPdfJob] = useState<PdfJobState>({ status: 'idle' });
  const [reportList, setReportList] = useState<ReportListItem[] | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const pollingRef = useRef<number | null>(null);

  // Load data: fetch list if no reportId, otherwise fetch summary
  useEffect(() => {
    if (!reportId) {
      setLoading(false);
      setListLoading(true);
      setError(null);
      fetchReportList()
        .then((res) => {
          setReportList(res.reports || []);
        })
        .catch((err: Error) => {
          setError(err?.message || '加载报告列表失败');
        })
        .finally(() => setListLoading(false));
      return;
    }
    setLoading(true);
    setError(null);
    fetchReportSummary(reportId)
      .then((res) => {
        setData(res);
      })
      .catch((err: Error) => {
        setError(err?.message || '加载报告失败，请稍后重试');
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current !== null) {
        window.clearTimeout(pollingRef.current);
      }
    };
  }, []);

  // ─── Download PDF flow ─────────────────────────────────────────

  const MAX_POLL_MS = 60_000; // 60s timeout, then show "please retry later"

  const handleDownloadPdf = useCallback(async () => {
    if (!reportId) return;
    setPdfJob({ status: 'creating' });
    try {
      const jobRes = await createPdfJob(reportId, data?.plan_type || 'advanced');
      if (!jobRes.job_id) {
        setPdfJob({ status: 'error', error: '创建任务失败' });
        return;
      }
      setPdfJob({ status: 'polling', jobId: jobRes.job_id });

      const startTime = Date.now();

      const poll = async (jobId: string) => {
        // Timeout protection — don't spin forever
        if (Date.now() - startTime > MAX_POLL_MS) {
          setPdfJob({
            status: 'error',
            error: '报告生成时间较长，请稍后在报告中心下载，或点击重试',
          });
          return;
        }
        try {
          const statusRes = await fetchPdfJobStatus(jobId);
          if (statusRes.status === 'completed' && statusRes.download_url) {
            setPdfJob({ status: 'ready', downloadUrl: statusRes.download_url });
            // Use hidden <a> click instead of window.open — avoids popup blockers
            const a = document.createElement('a');
            a.href = statusRes.download_url;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          } else if (statusRes.status === 'failed') {
            setPdfJob({ status: 'error', error: statusRes.error_message || 'PDF 生成失败' });
          } else {
            pollingRef.current = window.setTimeout(() => poll(jobId), 1500);
          }
        } catch {
          setPdfJob({ status: 'error', error: '查询任务状态失败' });
        }
      };
      poll(jobRes.job_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '下载失败';
      setPdfJob({ status: 'error', error: msg });
    }
  }, [reportId, data?.plan_type]);

  // ─── Share handler ─────────────────────────────────────────────

  const handleShare = useCallback(async () => {
    if (navigator.share) {
      try { await navigator.share({ title: '择境志愿分析报告', url: window.location.href }); } catch { /* ignore */ }
    } else {
      try { await navigator.clipboard.writeText(window.location.href); } catch { /* ignore */ }
    }
  }, []);

  // ─── Loading state ─────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner text="加载分析报告中..." size={48} />
      </div>
    );
  }

  // ─── Error state ───────────────────────────────────────────────

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-10 max-w-md w-full text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-5">
            <ShieldAlert className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="font-serif text-2xl text-[#1A2E22] mb-3">加载失败</h2>
          <p className="font-sans text-sm text-[#6B5E4E] mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2.5 bg-[#1A2E22] text-white rounded-xl text-sm font-medium hover:bg-brand-800 transition-colors"
          >
            重新加载
          </button>
        </motion.div>
      </div>
    );
  }

  // ─── Report list page (no reportId) ────────────────────────────

  if (!reportId && reportList !== null) {
    return (
      <>
        <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-28 md:pt-32 pb-24">
          {/* Header */}
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="font-serif text-3xl sm:text-4xl text-[#1A2E22] mb-3">
              志愿填报分析报告
            </h1>
            <p className="font-sans text-sm text-[#6B5E4E]">
              {reportList.length > 0
                ? `您有 ${reportList.length} 份历史报告，点击查看详情`
                : '暂无报告，请先完成志愿评估'}
            </p>
          </motion.div>

          {/* Report cards */}
          {reportList.length > 0 ? (
            <div className="space-y-4">
              {reportList.map((r, idx) => (
                <motion.button
                  key={r.report_id}
                  onClick={() => navigate(`/report/${r.report_id}`)}
                  className="w-full text-left bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5 sm:p-6 hover:border-[#A8883C] hover:shadow-md transition-all group cursor-pointer"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08, duration: 0.35 }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <BarChart3 className="w-4 h-4 text-[#A8883C] flex-shrink-0" />
                        <h3 className="font-serif text-lg text-[#1A2E22] truncate group-hover:text-[#A8883C] transition-colors">
                          {r.title || '志愿填报分析报告'}
                        </h3>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-sans text-xs text-[#6B5E4E]">
                        {r.province && (
                          <span className="inline-flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {r.province}
                          </span>
                        )}
                        {r.score != null && (
                          <span className="font-medium text-[#1A2E22]">{r.score}分</span>
                        )}
                        {r.rank != null && (
                          <span>位次 {r.rank.toLocaleString()}</span>
                        )}
                        {r.subject_type && (
                          <span className="bg-beige-100 text-beige-700 px-2 py-0.5 rounded-full text-[11px]">
                            {r.subject_type === 'physics' ? '物理类' : r.subject_type === 'history' ? '历史类' : r.subject_type}
                          </span>
                        )}
                        {r.created_at && (
                          <span className="inline-flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(r.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[#C4B89A] group-hover:text-[#A8883C] transition-colors flex-shrink-0 mt-1" />
                  </div>
                </motion.button>
              ))}
            </div>
          ) : (
            /* No reports yet */
            <motion.div
              className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-10 text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="w-16 h-16 rounded-full bg-beige-100 flex items-center justify-center mx-auto mb-5">
                <FileText className="w-8 h-8 text-beige-400" />
              </div>
              <p className="font-sans text-sm text-[#6B5E4E] mb-6">
                请先在志愿评估中输入分数和位次，AI 将为你生成专属冲稳保分析报告
              </p>
              <button
                onClick={() => navigate('/calculator')}
                className="px-6 py-2.5 bg-[#1A2E22] text-white rounded-xl text-sm font-medium hover:bg-brand-800 transition-colors"
              >
                开始评估
              </button>
            </motion.div>
          )}

          {/* New assessment CTA */}
          {reportList.length > 0 && (
            <motion.div
              className="mt-8 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              <button
                onClick={() => navigate('/calculator')}
                className="inline-flex items-center gap-2 px-6 py-2.5 border border-[#A8883C] text-[#A8883C] rounded-xl text-sm font-medium hover:bg-beige-50 transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                新建评估
              </button>
            </motion.div>
          )}
        </div>
      </>
    );
  }

  // ─── Loading state ─────────────────────────────────────────────

  if (listLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  // ─── Error state ───────────────────────────────────────────────

  if (error && !reportId) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-10 max-w-md w-full text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="font-sans text-sm text-red-500 mb-4">{error}</p>
          <button
            onClick={() => navigate('/calculator')}
            className="px-6 py-2.5 bg-[#1A2E22] text-white rounded-xl text-sm font-medium"
          >
            开始评估
          </button>
        </motion.div>
      </div>
    );
  }

  // ─── Not found / no data (has reportId) ────────────────────────

  if (!data || !data.success) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-10 max-w-md w-full text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-16 h-16 rounded-full bg-beige-100 flex items-center justify-center mx-auto mb-5">
            <FileText className="w-8 h-8 text-beige-400" />
          </div>
          <h2 className="font-serif text-2xl text-[#1A2E22] mb-3">
            {reportId ? '未找到报告' : '志愿填报分析报告'}
          </h2>
          <p className="font-sans text-sm text-[#6B5E4E] mb-6">
            {reportId
              ? '该报告不存在或已被删除'
              : '请先在志愿评估中输入分数和位次，AI 将为你生成专属冲稳保分析报告'}
          </p>
          <button
            onClick={() => navigate(reportId ? '/preview' : '/calculator')}
            className="px-6 py-2.5 bg-[#1A2E22] text-white rounded-xl text-sm font-medium hover:bg-brand-800 transition-colors"
          >
            {reportId ? '返回推荐' : '开始评估'}
          </button>
        </motion.div>
      </div>
    );
  }

  const summary: ReportSummary = data.summary;
  const profile: StudentProfile = summary.student_profile;
  const exec: ExecutiveSummary = summary.executive_summary;
  const bucket: BucketSummary = summary.bucket_summary;
  const risks: RiskPreviewItem[] = summary.risk_preview || [];
  const candidates: KeyCandidatePreview[] = summary.key_candidates_preview || [];
  const canDownload = summary.download_permission?.can_download_pdf || false;

  const totalBucket = bucket.rush.count + bucket.stable.count + bucket.safe.count;

  // ─── Render loaded page ────────────────────────────────────────

  return (
    <>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-28 md:pt-32 pb-24">

        {/* Back button */}
        <motion.button
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-sm text-[#6B5E4E] hover:text-[#1A2E22] transition-colors mb-6 font-sans"
        >
          <ArrowLeft className="w-4 h-4" />
          返回
        </motion.button>

        {/* Title area */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          <h1 className="font-serif text-3xl font-normal text-[#1A2E22] mb-2">
            择境志愿填报分析报告
          </h1>
          <div className="flex items-center gap-3 font-sans text-sm text-[#6B5E4E]">
            {profile.generated_at && (
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" />
                {profile.generated_at.slice(0, 10)}
              </span>
            )}
            <PlanBadge planType={data.plan_type} />
          </div>
        </motion.div>

        {/* ── Hero Summary Card ─────────────────────────────────── */}
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <h2 className="font-serif text-xl text-[#1A2E22] mb-1">核心结论</h2>
            <p className="font-serif text-2xl text-[#A8883C] italic mb-4">{exec.headline}</p>
          </motion.div>

          <motion.div variants={itemVariants} className="mb-4">
            <p className="font-sans text-sm text-[#4A4A4A] leading-relaxed">{exec.key_finding}</p>
          </motion.div>

          {/* Opportunities */}
          {exec.opportunities && exec.opportunities.length > 0 && (
            <motion.div variants={itemVariants} className="mb-4">
              <p className="font-sans text-xs font-medium text-[#1A2E22] uppercase tracking-wider mb-2">机会</p>
              <ul className="space-y-1.5">
                {exec.opportunities.map((op, i) => (
                  <li key={i} className="flex items-start gap-2 font-sans text-sm text-[#4A4A4A]">
                    <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                    {op}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Risks */}
          {exec.risks && exec.risks.length > 0 && (
            <motion.div variants={itemVariants} className="p-4 rounded-xl bg-red-50/60 border border-red-100">
              <p className="font-sans text-xs font-medium text-red-700 uppercase tracking-wider mb-2">风险</p>
              <ul className="space-y-1.5">
                {exec.risks.map((risk, i) => (
                  <li key={i} className="flex items-start gap-2 font-sans text-sm text-red-700">
                    <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                    {risk}
                  </li>
                ))}
              </ul>
            </motion.div>
          )}
        </motion.div>

        {/* ── Student Profile Card ──────────────────────────────── */}
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <h2 className="font-serif text-xl text-[#1A2E22] mb-4 flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-[#A8883C]" />
              考生档案
            </h2>
          </motion.div>

          <motion.div variants={itemVariants} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3 rounded-xl bg-beige-50">
              <p className="font-sans text-xs text-[#6B5E4E] mb-0.5">省份</p>
              <p className="font-serif text-lg text-[#1A2E22]">{profile.province}</p>
            </div>
            <div className="p-3 rounded-xl bg-beige-50">
              <p className="font-sans text-xs text-[#6B5E4E] mb-0.5">科类</p>
              <p className="font-serif text-lg text-[#1A2E22]">{profile.subject_type}</p>
            </div>
            <div className="p-3 rounded-xl bg-beige-50">
              <p className="font-sans text-xs text-[#6B5E4E] mb-0.5">分数</p>
              <p className="font-serif text-lg text-[#1A2E22]">{profile.score} 分</p>
            </div>
            <div className="p-3 rounded-xl bg-beige-50">
              <p className="font-sans text-xs text-[#6B5E4E] mb-0.5">位次</p>
              <p className="font-serif text-lg text-[#1A2E22]">{profile.rank.toLocaleString('zh-CN')}</p>
            </div>
          </motion.div>

          {(profile.strategy || profile.total_candidates > 0) && (
            <motion.div variants={itemVariants} className="mt-4 flex flex-wrap gap-4 text-sm font-sans text-[#6B5E4E]">
              {profile.strategy && (
                <span className="flex items-center gap-1.5">
                  <Flag className="w-3.5 h-3.5" /> 策略: {profile.strategy}
                </span>
              )}
              {profile.total_candidates > 0 && (
                <span className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5" /> 候选方案: {profile.total_candidates}
                </span>
              )}
            </motion.div>
          )}
        </motion.div>

        {/* ── Bucket Overview ───────────────────────────────────── */}
        <motion.div
          className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <h2 className="font-serif text-xl text-[#1A2E22] mb-4">冲稳保结构</h2>
          </motion.div>

          <motion.div variants={itemVariants} className="space-y-4">
            {/* Rush */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-sans text-sm font-medium text-[#4A4A4A]">冲 (冲刺)</span>
                <span className="font-sans text-sm text-[#6B5E4E]">{bucket.rush.count} 所</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-beige-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-500 transition-all duration-700"
                  style={{ width: `${totalBucket > 0 ? (bucket.rush.count / totalBucket) * 100 : 0}%` }}
                />
              </div>
              {bucket.rush.description && (
                <p className="font-sans text-xs text-[#6B5E4E] mt-1">{bucket.rush.description}</p>
              )}
            </div>

            {/* Stable */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-sans text-sm font-medium text-[#4A4A4A]">稳 (稳妥)</span>
                <span className="font-sans text-sm text-[#6B5E4E]">{bucket.stable.count} 所</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-beige-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                  style={{ width: `${totalBucket > 0 ? (bucket.stable.count / totalBucket) * 100 : 0}%` }}
                />
              </div>
              {bucket.stable.description && (
                <p className="font-sans text-xs text-[#6B5E4E] mt-1">{bucket.stable.description}</p>
              )}
            </div>

            {/* Safe */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-sans text-sm font-medium text-[#4A4A4A]">保 (保底)</span>
                <span className="font-sans text-sm text-[#6B5E4E]">{bucket.safe.count} 所</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-beige-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-amber-500 transition-all duration-700"
                  style={{ width: `${totalBucket > 0 ? (bucket.safe.count / totalBucket) * 100 : 0}%` }}
                />
              </div>
              {bucket.safe.description && (
                <p className="font-sans text-xs text-[#6B5E4E] mt-1">{bucket.safe.description}</p>
              )}
            </div>

            {bucket.total_recommended > 0 && (
              <div className="pt-3 border-t border-[#E0D8CC]">
                <div className="flex items-center justify-between">
                  <span className="font-sans text-sm text-[#6B5E4E]">合计推荐</span>
                  <span className="font-mono text-sm font-medium text-[#1A2E22]">{bucket.total_recommended} 所</span>
                </div>
              </div>
            )}
          </motion.div>
        </motion.div>

        {/* ── Risk Preview ──────────────────────────────────────── */}
        {risks.length > 0 && (
          <motion.div
            className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={itemVariants}>
              <h2 className="font-serif text-xl text-[#1A2E22] mb-4 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-500" />
                风险预览
              </h2>
            </motion.div>

            <motion.div variants={itemVariants} className="space-y-3">
              {risks.slice(0, 3).map((risk, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-[#E0D8CC] last:border-0">
                  <span className="font-sans text-sm text-[#4A4A4A]">{risk.risk_type}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium font-sans ${getSeverityStyle(risk.severity)}`}>
                    {risk.severity}
                  </span>
                </div>
              ))}
            </motion.div>
          </motion.div>
        )}

        {/* ── Key Candidates Preview ────────────────────────────── */}
        {candidates.length > 0 && (
          <motion.div
            className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={itemVariants}>
              <h2 className="font-serif text-xl text-[#1A2E22] mb-4 flex items-center gap-2">
                <Flag className="w-5 h-5 text-[#A8883C]" />
                重点院校预览
              </h2>
            </motion.div>

            <motion.div variants={itemVariants} className="space-y-3">
              {candidates.slice(0, 5).map((c, i) => (
                <div key={i} className="flex items-center justify-between py-3 border-b border-[#E0D8CC] last:border-0">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="font-sans text-sm font-medium text-[#4A4A4A] truncate">{c.school_name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 font-sans ${getTierStyle(c.tier)}`}>
                      {c.tier}
                    </span>
                    {c.school_level && (
                      <span className="font-sans text-xs text-[#6B5E4E] hidden sm:inline">{c.school_level}</span>
                    )}
                  </div>
                  <span className={`font-mono text-sm font-medium shrink-0 ml-3 ${
                    c.score_gap > 0 ? 'text-red-500' : c.score_gap < 0 ? 'text-emerald-600' : 'text-[#6B5E4E]'
                  }`}>
                    {c.score_gap > 0 ? '+' : ''}{c.score_gap} 分
                  </span>
                </div>
              ))}
            </motion.div>
          </motion.div>
        )}

        {/* ── Download PDF CTA ──────────────────────────────────── */}
        {canDownload ? (
          <motion.div
            className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6 text-center"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={itemVariants}>
              <div className="w-14 h-14 rounded-full bg-[#A8883C]/10 flex items-center justify-center mx-auto mb-4">
                <FileText className="w-7 h-7 text-[#A8883C]" />
              </div>
              <h3 className="font-serif text-xl text-[#1A2E22] mb-2">🏆 下载完整 PDF 分析报告</h3>
              <p className="font-sans text-sm text-[#6B5E4E] mb-6">
                包含完整数据、风险清单、建议
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-3 justify-center">
                <button
                  onClick={() => navigate(`/report/pdf-preview/${reportId}`)}
                  className="inline-flex items-center gap-2 bg-white border border-[#1A2E22] text-[#1A2E22] rounded-xl px-6 py-3 text-base font-medium hover:bg-[#F5F0E8] transition-all"
                >
                  <FileText className="w-5 h-5" />
                  查看完整报告
                </button>
              <button
                onClick={handleDownloadPdf}
                disabled={pdfJob.status === 'creating' || pdfJob.status === 'polling'}
                className="inline-flex items-center gap-2 bg-[#A8883C] hover:bg-[#8E7030] text-white rounded-xl px-6 py-3 text-base font-medium shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {pdfJob.status === 'creating' || pdfJob.status === 'polling' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    下载 PDF 报告
                  </>
                )}
              </button>
              </div>
              {pdfJob.status === 'error' && pdfJob.error && (
                <div className="mt-3 space-y-2">
                  <p className="font-sans text-xs text-red-500">{pdfJob.error}</p>
                  <button
                    onClick={handleDownloadPdf}
                    className="font-sans text-xs text-[#A8883C] underline hover:text-[#8E7030] transition-colors"
                  >
                    重新生成
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        ) : (
          /* ── Locked Section ─────────────────────────────────────── */
          <motion.div
            className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-6 sm:p-8 mb-6 text-center relative overflow-hidden"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <div className="absolute inset-0 bg-beige-50/80 backdrop-blur-[2px] flex items-center justify-center z-10">
              <motion.div variants={itemVariants} className="text-center">
                <Lock className="w-8 h-8 text-[#A8883C] mx-auto mb-3" />
                <p className="font-serif text-lg text-[#1A2E22] mb-2">升级解锁更多分析内容</p>
                <p className="font-sans text-xs text-[#6B5E4E] mb-4">PDF 报告及完整数据仅对付费用户开放</p>
                <button
                  onClick={() => navigate('/pricing')}
                  className="inline-flex items-center gap-2 bg-[#A8883C] hover:bg-[#8E7030] text-white rounded-xl px-5 py-2.5 text-sm font-medium shadow-sm transition-all"
                >
                  <Sparkles className="w-4 h-4" />
                  查看版本
                </button>
              </motion.div>
            </div>
            <div className="opacity-30 pointer-events-none">
              <FileText className="w-14 h-14 text-beige-300 mx-auto mb-4" />
              <h3 className="font-serif text-xl text-[#1A2E22] mb-2">🏆 下载完整 PDF 分析报告</h3>
              <p className="font-sans text-sm text-[#6B5E4E] mb-6">包含完整数据、风险清单、建议</p>
              <div className="inline-flex items-center gap-2 bg-beige-200 text-beige-500 rounded-xl px-6 py-3 text-base font-medium">
                下载 PDF 报告
              </div>
            </div>
          </motion.div>
        )}

        {/* ── Actions ────────────────────────────────────────────── */}
        <motion.div
          className="flex flex-wrap items-center justify-center gap-3 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1A2E22] text-white rounded-xl text-sm font-medium hover:bg-brand-800 transition-colors shadow-sm"
          >
            <Sparkles className="w-4 h-4" />
            问 AI
          </button>
          <button
            onClick={() => navigate('/preview')}
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-[#E0D8CC] bg-white text-[#4A4A4A] rounded-xl text-sm font-medium hover:bg-beige-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            返回推荐
          </button>
          <button
            onClick={handleShare}
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-[#E0D8CC] bg-white text-[#4A4A4A] rounded-xl text-sm font-medium hover:bg-beige-50 transition-colors"
          >
            <Share2 className="w-4 h-4" />
            分享
          </button>
        </motion.div>

        {/* ── Disclaimer ──────────────────────────────────────────── */}
        <motion.p
          className="text-center font-sans text-xs text-[#6B5E4E] leading-relaxed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.5 }}
        >
          本报告由择境 AI 志愿系统生成，数据来源于各省教育考试院及教育部官方公布信息。<br />
          报告内容仅供填报参考，不构成最终填报建议。请结合个人实际情况做出决策。
        </motion.p>
      </div>
    </>
  );
}
