import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft, Download, ShieldAlert, FileText,
  AlertTriangle, CheckCircle, MapPin, GraduationCap, BookOpen,
  ExternalLink, Loader2, Sparkles, Building2, TrendingUp, Shield,
  Award, Layers, BarChart3, Target, Globe, Clock, Users, Zap
} from 'lucide-react';
import { fetchPdfData, createPdfJob, fetchPdfJobStatus } from '../services/reportService';
import type { PdfDataResponse } from '../services/reportService';
import LoadingSpinner from '../components/ui/LoadingSpinner';

/* ============================================================
   PDF PREVIEW PAGE — 择境 ZENPATH Editorial Report
   Designed for A4 print via Playwright headless Chromium
   ============================================================ */

// ── Types ────────────────────────────────────────────────────

interface PdfJobState {
  status: 'idle' | 'creating' | 'polling' | 'completed' | 'error';
  url?: string;
  error?: string;
}

// ── Helper Components ────────────────────────────────────────

function SectionHeading({ num, title }: { num: string; title: string }) {
  return (
    <div className="pb-8 mb-12 border-b border-[#E8E3DA] flex items-center gap-4 print:page-break-before">
      <div className="w-7 h-7 rounded-full bg-[#1A2E22] flex items-center justify-center shrink-0">
        <span className="text-white text-[11px] font-medium tracking-wider">{num}</span>
      </div>
      <h2 className="font-serif text-[36px] leading-[1.15] tracking-[-0.01em] font-light text-[#1A2E22]">
        {title}
      </h2>
      <div className="w-[6px] h-[6px] rounded-full bg-[#A8883C] animate-pulse ml-auto shrink-0" />
    </div>
  );
}

function StatBox({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className={accent ? 'border-l-2 border-[#A8883C] pl-4' : ''}>
      <p className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#8A8A8A] mb-1">{label}</p>
      <p className="font-serif text-[22px] leading-[1.3] font-light text-[#1A1A1A]">{value}</p>
    </div>
  );
}

function AiNarrativeCard({ text, title }: { text?: string; title?: string }) {
  if (!text || text.trim().length === 0) return null;
  return (
    <div className="bg-gradient-to-br from-[#A8883C]/3 to-[#1A2E22]/2 border border-[#A8883C]/10 p-10 rounded-none">
      <div className="flex items-center gap-2 mb-5">
        <Sparkles size={14} className="text-[#A8883C]" />
        <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#A8883C]">
          {title || 'AI 综合分析'}
        </span>
      </div>
      <p className="font-sans text-[15px] leading-[1.8] text-[#1A1A1A] whitespace-pre-line">{text}</p>
    </div>
  );
}

function AnalysisRow({ icon: Icon, label, text }: { icon: React.ElementType; label: string; text?: string }) {
  if (!text || text.trim().length === 0) return null;
  return (
    <div className="flex gap-3 items-start mb-4">
      <Icon size={16} className="text-[#A8883C] mt-0.5 shrink-0" />
      <div>
        <p className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#8A8A8A] mb-0.5">{label}</p>
        <p className="font-sans text-[15px] leading-[1.75] text-[#1A1A1A]">{text}</p>
      </div>
    </div>
  );
}

function EvidenceSection({ items }: { items?: { title: string; source_url: string; doc_type: string }[] }) {
  if (!items || items.length === 0) return null;
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="mt-6 border border-[#E8E3DA] rounded-none">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-3 font-sans text-[13px] text-[#5A5A5A] hover:bg-[#F8F6F1] transition-colors"
      >
        <span className="flex items-center gap-2">
          <FileText size={14} className="text-[#A8883C]" />
          参考资料 ({items.length})
        </span>
        <span className="text-[#A8883C] text-[18px] leading-none">{expanded ? '–' : '+'}</span>
      </button>
      {expanded && (
        <div className="border-t border-[#E8E3DA] divide-y divide-[#E8E3DA]">
          {items.map((item, i) => (
            <div key={i} className="px-5 py-3 flex items-start gap-3">
              <FileText size={13} className="text-[#A8883C] mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="font-sans text-[14px] text-[#1A1A1A] truncate">{item.title || '参考资料'}</p>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-sans text-[12px] text-[#A8883C] hover:underline inline-flex items-center gap-1"
                  >
                    {item.source_url} <ExternalLink size={10} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WarningSection({ items }: { items?: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="mt-4 bg-[#C0392B]/5 border border-[#C0392B]/20 p-5 rounded-none">
      {items.map((w, i) => (
        <div key={i} className="flex items-start gap-2 mb-2 last:mb-0">
          <AlertTriangle size={14} className="text-[#C0392B] shrink-0 mt-0.5" />
          <p className="font-sans text-[13px] text-[#C0392B]">{w}</p>
        </div>
      ))}
    </div>
  );
}

// ── Fallback image handler ──────────────────────────────────

function SchoolLogo({ src, alt }: { src?: string; alt: string }) {
  const [error, setError] = useState(false);
  if (!src || error) {
    return (
      <div className="w-16 h-16 rounded-lg bg-[#F8F6F1] flex items-center justify-center">
        <Building2 size={24} className="text-[#8A8A8A]" />
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={alt}
      className="w-16 h-16 rounded-lg object-contain bg-[#F8F6F1]"
      onError={() => setError(true)}
    />
  );
}

// ── Format helpers ──────────────────────────────────────────

function formatDate(iso?: string): string {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}年${m}月${day}日`;
  } catch {
    return '';
  }
}

// ── Main Page Component ─────────────────────────────────────

export default function PdfPreview() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<PdfDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [pdfJob, setPdfJob] = useState<PdfJobState>({ status: 'idle' });

  // ── Fetch report data ─────────────────────────────────────

  useEffect(() => {
    if (!reportId) {
      setError('缺少报告ID');
      setLoading(false);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        setLoading(true);
        const res = await fetchPdfData(reportId);
        if (cancelled) return;
        if (!res.success) {
          setError('数据加载失败');
          return;
        }
        setData(res);
      } catch (err: any) {
        if (!cancelled) setError(err?.message || '网络请求出错');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [reportId]);

  // ── PDF Ready signal for Playwright ───────────────────────

  useEffect(() => {
    if (!data || loading) return;

    requestAnimationFrame(() => {
      setTimeout(async () => {
        try {
          await Promise.race([
            document.fonts.ready,
            new Promise<void>((resolve) => setTimeout(resolve, 8000)),
          ]);
        } catch {
          /* ignore */
        }
        (window as any).__ZENPATH_PDF_READY__ = true;
      }, 500);
    });
  }, [data, loading]);

  // ── PDF Download logic ────────────────────────────────────

  const handleDownload = async () => {
    if (!reportId) return;
    setPdfJob({ status: 'creating' });

    try {
      const job = await createPdfJob(reportId);
      setPdfJob({ status: 'polling' });

      const maxPolls = 40; // 60s timeout
      for (let i = 0; i < maxPolls; i++) {
        await new Promise<void>((r) => setTimeout(r, 1500));
        const status = await fetchPdfJobStatus(job.job_id!);
        if (status.status === 'completed') {
          setPdfJob({ status: 'completed', url: status.download_url });
          // Trigger download
          const a = document.createElement('a');
          a.href = status.download_url!;
          a.download = `zenpath-report-${reportId}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return;
        }
        if (status.status === 'failed') {
          setPdfJob({ status: 'error', error: status.error_message || '生成失败' });
          return;
        }
      }
      setPdfJob({ status: 'error', error: '生成超时，请稍后重试' });
    } catch (err: any) {
      setPdfJob({ status: 'error', error: err?.message || '下载请求失败' });
    }
  };

  // ── Extract report data ───────────────────────────────────

  const r = (data as any)?.report || (data as any);
  const brand = data?.branding;
  const printSettings = data?.print_settings;

  // ── Loading state ─────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4">
        <LoadingSpinner />
        <p className="font-sans text-[14px] text-[#5A5A5A]">正在生成报告...</p>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────

  if (error || !data) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <ShieldAlert size={48} className="mx-auto mb-4 text-[#C0392B]" />
          <h2 className="font-serif text-[28px] font-light text-[#1A2E22] mb-3">报告加载失败</h2>
          <p className="font-sans text-[15px] text-[#5A5A5A] mb-6">{error || '无法获取报告数据'}</p>
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 font-sans text-[14px] text-white bg-[#1A2E22] px-6 py-3 rounded-none hover:bg-[#1A2E22]/90 transition-colors"
          >
            <ArrowLeft size={16} />
            返回
          </button>
        </div>
      </div>
    );
  }

  // ── Destructure report ────────────────────────────────────

  const executive_summary = r?.executive_summary;
  const student_profile = r?.student_profile;
  const score_positioning = r?.score_positioning;
  const bucket_summary = r?.bucket_summary;
  const volunteer_strategy = r?.volunteer_strategy;
  const key_candidates: any[] = r?.key_candidates || [];
  const school_deep_dives: any[] = r?.school_deep_dives || [];
  const major_match_analysis = r?.major_match_analysis;
  const adjustment_risk_analysis = r?.adjustment_risk_analysis;
  const region_analysis = r?.region_analysis;
  const school_tier_analysis = r?.school_tier_analysis;
  const rag_evidence_sections: any[] = r?.rag_evidence_sections || [];
  const risk_register: any[] = r?.risk_register || [];
  const final_recommendations: any[] = r?.final_recommendations || [];
  const checklist: any[] = r?.checklist || [];
  const data_sources = r?.data_sources;
  const disclaimer = r?.disclaimer;
  const ai_narratives = r?.ai_narratives;
  const generated_at = r?.generated_at;

  const sectionFade = {
    initial: { opacity: 0, y: 40 },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, margin: '-60px' },
    transition: { duration: 0.9, ease: [0.22, 0.61, 0.36, 1] },
  };

  const stagger = {
    whileInView: { transition: { staggerChildren: 0.1 } },
    viewport: { once: true },
  };

  // ── Render ────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-white" style={{ WebkitPrintColorAdjust: 'exact', printColorAdjust: 'exact' } as React.CSSProperties}>
      {/* ── Fixed Header ──────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white/90 backdrop-blur-xl border-b border-[#E8E3DA] z-50 print:hidden">
        <div className="max-w-[920px] mx-auto px-8 h-full flex items-center justify-between">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 font-sans text-[13px] text-[#5A5A5A] hover:text-[#1A2E22] transition-colors"
          >
            <ArrowLeft size={16} />
            返回
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 font-sans text-[13px] text-[#5A5A5A] border border-[#E8E3DA] px-4 py-2 rounded-none hover:bg-[#F8F6F1] transition-colors"
            >
              <FileText size={14} />
              打印
            </button>
            <button
              onClick={handleDownload}
              disabled={pdfJob.status === 'creating' || pdfJob.status === 'polling'}
              className="inline-flex items-center gap-2 font-sans text-[13px] text-white bg-[#A8883C] px-4 py-2 rounded-none hover:bg-[#C4A45C] transition-colors disabled:opacity-60"
            >
              {pdfJob.status === 'creating' || pdfJob.status === 'polling' ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Download size={14} />
              )}
              下载 PDF
            </button>
          </div>
        </div>
      </header>

      {/* ── PDF Download error toast ─────────────────────── */}
      {pdfJob.status === 'error' && (
        <div className="fixed top-20 right-8 z-50 bg-white border border-[#C0392B]/30 shadow-[0_2px_12px_rgba(0,0,0,0.08)] px-5 py-3 print:hidden">
          <div className="flex items-center gap-3">
            <AlertTriangle size={14} className="text-[#C0392B]" />
            <p className="font-sans text-[13px] text-[#C0392B]">{pdfJob.error}</p>
            <button
              onClick={handleDownload}
              className="font-sans text-[12px] text-[#A8883C] hover:underline ml-2"
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* ── Content wrapper with header offset ───────────── */}
      <div className="pt-16">
        {/* ============================================================
             COVER PAGE — Dark full-viewport splash
             ============================================================ */}
        <section className="min-h-screen bg-[#1A2E22] flex flex-col items-center justify-center text-center px-8 py-20"
          style={{ WebkitPrintColorAdjust: 'exact', printColorAdjust: 'exact' } as React.CSSProperties}
        >
          <div className="max-w-[600px]">
            <p className="font-sans text-[11px] tracking-[0.3em] uppercase text-[#A8883C] mb-8">
              择境 ZENPATH
            </p>

            <h1 className="font-serif text-[56px] leading-[1.05] tracking-[-0.02em] font-light text-white mb-10 text-balance">
              志愿填报分析报告
            </h1>

            {/* Gold decorative lines — short-long-short */}
            <div className="flex flex-col items-center gap-2 mb-10 pointer-events-none">
              <div className="w-16 h-[1px] bg-[#A8883C]" />
              <div className="w-32 h-[1px] bg-[#A8883C]" />
              <div className="w-16 h-[1px] bg-[#A8883C]" />
            </div>

            {student_profile && (
              <>
                <p className="font-sans text-[15px] text-white/80 mb-4">
                  {student_profile.province} · {student_profile.subject_type}
                </p>
                <p className="font-serif text-[32px] leading-[1.2] font-light text-white mb-2">
                  {student_profile.score}分 · 全省{student_profile.rank}名
                </p>
                {student_profile.total_candidates && (
                  <p className="font-sans text-[13px] text-white/50">
                    考生总数: {student_profile.total_candidates.toLocaleString()}
                  </p>
                )}
              </>
            )}

            <p className="font-mono text-[11px] tracking-[0.05em] text-white/40 mt-16">
              2026年6月
            </p>
          </div>
        </section>

        {/* Gold gradient divider after cover */}
        <div className="h-[1px] bg-gradient-to-r from-transparent via-[#A8883C]/30 to-transparent pointer-events-none" />

        {/* ============================================================
             SECTION 1 — 核心结论 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="01" title="核心结论" />

            {executive_summary && (
              <AiNarrativeCard text={ai_narratives?.executive_summary} title="AI 综合评估" />
            )}

            {executive_summary?.headline && (
              <p className="font-serif text-[22px] italic leading-[1.45] text-[#A8883C] mt-8 mb-4 text-pretty">
                "{executive_summary.headline}"
              </p>
            )}

            {executive_summary?.key_finding && (
              <p className="font-sans text-[16px] leading-[1.75] text-[#1A1A1A] mb-8 text-pretty">
                {executive_summary.key_finding}
              </p>
            )}

            {/* Opportunities */}
            {executive_summary?.opportunities && executive_summary.opportunities.length > 0 && (
              <div className="mb-8">
                <h3 className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#2D5A3E] mb-4 flex items-center gap-2">
                  <CheckCircle size={14} className="text-[#2D5A3E]" />
                  机遇
                </h3>
                <ol className="space-y-2">
                  {executive_summary.opportunities.map((opp: string, i: number) => (
                    <li key={i} className="flex items-start gap-3 font-sans text-[15px] text-[#1A1A1A]">
                      <span className="w-5 h-5 rounded-full bg-[#2D5A3E]/10 text-[#2D5A3E] text-[11px] flex items-center justify-center shrink-0 mt-0.5 font-medium">
                        {i + 1}
                      </span>
                      {opp}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Risks */}
            {executive_summary?.risks && executive_summary.risks.length > 0 && (
              <div className="border border-[#B8860B]/30 bg-[#B8860B]/5 p-6 rounded-none">
                <h3 className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#B8860B] mb-3 flex items-center gap-2">
                  <AlertTriangle size={14} className="text-[#B8860B]" />
                  风险提示
                </h3>
                <ul className="space-y-2">
                  {executive_summary.risks.map((risk: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 font-sans text-[14px] text-[#5A5A5A]">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#B8860B] mt-2 shrink-0" />
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {executive_summary?.next_step && (
              <div className="mt-6 border-l-2 border-[#A8883C] pl-4 py-2">
                <p className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#8A8A8A] mb-1">下一步行动</p>
                <p className="font-sans text-[15px] text-[#1A1A1A]">{executive_summary.next_step}</p>
              </div>
            )}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 2 — 成绩定位 (subtle)
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="02" title="成绩定位" />

            {/* 4 stat row */}
            {student_profile && (
              <div className="grid grid-cols-4 gap-8 mb-8">
                <StatBox label="省份" value={student_profile.province} />
                <StatBox label="科目类" value={student_profile.subject_type} />
                <StatBox label="分数" value={`${student_profile.score}分`} accent />
                <StatBox label="排名" value={`全省${student_profile.rank}名`} accent />
              </div>
            )}

            {student_profile?.strategy && (
              <div className="border-l-2 border-[#A8883C] pl-4 py-2 mb-8">
                <p className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#8A8A8A] mb-1">填报策略</p>
                <p className="font-sans text-[15px] text-[#1A1A1A]">{student_profile.strategy}</p>
              </div>
            )}

            <AiNarrativeCard text={ai_narratives?.score_positioning} title="成绩定位分析" />
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 3 — 冲稳保结构 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="03" title="冲稳保结构" />

            {bucket_summary && (
              <>
                {/* Rush — gold */}
                {bucket_summary.rush && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#A8883C]">冲</span>
                        <span className="font-mono text-[13px] text-[#A8883C]">{bucket_summary.rush.count}个</span>
                      </div>
                      {bucket_summary.total_recommended && (
                        <span className="font-mono text-[12px] text-[#8A8A8A]">
                          {Math.round((bucket_summary.rush.count / bucket_summary.total_recommended) * 100)}%
                        </span>
                      )}
                    </div>
                    <div className="h-1 w-full bg-[#F0EDE6] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#A8883C] rounded-full"
                        style={{ width: bucket_summary.total_recommended ? `${(bucket_summary.rush.count / bucket_summary.total_recommended) * 100}%` : '0%' }}
                      />
                    </div>
                    {bucket_summary.rush.description && (
                      <p className="font-sans text-[13px] text-[#5A5A5A] mt-2">{bucket_summary.rush.description}</p>
                    )}
                  </div>
                )}

                {/* Stable — emerald */}
                {bucket_summary.stable && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#2D5A3E]">稳</span>
                        <span className="font-mono text-[13px] text-[#2D5A3E]">{bucket_summary.stable.count}个</span>
                      </div>
                      {bucket_summary.total_recommended && (
                        <span className="font-mono text-[12px] text-[#8A8A8A]">
                          {Math.round((bucket_summary.stable.count / bucket_summary.total_recommended) * 100)}%
                        </span>
                      )}
                    </div>
                    <div className="h-1 w-full bg-[#F0EDE6] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#2D5A3E] rounded-full"
                        style={{ width: bucket_summary.total_recommended ? `${(bucket_summary.stable.count / bucket_summary.total_recommended) * 100}%` : '0%' }}
                      />
                    </div>
                    {bucket_summary.stable.description && (
                      <p className="font-sans text-[13px] text-[#5A5A5A] mt-2">{bucket_summary.stable.description}</p>
                    )}
                  </div>
                )}

                {/* Safe — blue */}
                {bucket_summary.safe && (
                  <div className="mb-8">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#1A2E22]">保</span>
                        <span className="font-mono text-[13px] text-[#1A2E22]">{bucket_summary.safe.count}个</span>
                      </div>
                      {bucket_summary.total_recommended && (
                        <span className="font-mono text-[12px] text-[#8A8A8A]">
                          {Math.round((bucket_summary.safe.count / bucket_summary.total_recommended) * 100)}%
                        </span>
                      )}
                    </div>
                    <div className="h-1 w-full bg-[#F0EDE6] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#1A2E22] rounded-full"
                        style={{ width: bucket_summary.total_recommended ? `${(bucket_summary.safe.count / bucket_summary.total_recommended) * 100}%` : '0%' }}
                      />
                    </div>
                    {bucket_summary.safe.description && (
                      <p className="font-sans text-[13px] text-[#5A5A5A] mt-2">{bucket_summary.safe.description}</p>
                    )}
                  </div>
                )}

                {bucket_summary.total_recommended && (
                  <div className="text-center border-t border-[#E8E3DA] pt-6">
                    <p className="font-sans text-[13px] text-[#8A8A8A]">
                      合计推荐: <span className="font-serif text-[22px] text-[#1A2E22] font-light">{bucket_summary.total_recommended}</span> 个专业组
                    </p>
                  </div>
                )}
              </>
            )}

            <div className="mt-8">
              <AiNarrativeCard text={ai_narratives?.bucket_analysis} title="冲稳保策略分析" />
            </div>
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 4 — 院校详解 (subtle) — THE KEY SECTION
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="04" title="院校详解" />

            {school_deep_dives.length === 0 && key_candidates.length > 0 && (
              <p className="font-sans text-[15px] text-[#5A5A5A] italic">正在加载院校详情...</p>
            )}

            {school_deep_dives.map((school: any, idx: number) => (
              <motion.div key={idx} className="mb-16 last:mb-0" {...stagger}>
                {/* School header row */}
                <div className="flex items-center gap-5 mb-6">
                  <SchoolLogo src={school.school_logo_url} alt={school.school_name} />
                  <div>
                    <h3 className="font-serif text-[28px] leading-[1.2] font-light text-[#1A2E22]">
                      {school.school_name}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      {/* Badges */}
                      {school.school_badges?.map((badge: string, bi: number) => (
                        <span
                          key={bi}
                          className="inline-block font-sans text-[11px] tracking-[0.02em] text-[#A8883C] border border-[#A8883C]/30 px-2.5 py-0.5"
                        >
                          {badge}
                        </span>
                      ))}
                      {school.bucket && (
                        <span className={`inline-block font-sans text-[11px] tracking-[0.02em] px-2.5 py-0.5 border ${
                          school.bucket === '冲' ? 'text-[#A8883C] border-[#A8883C]/30' :
                          school.bucket === '稳' ? 'text-[#2D5A3E] border-[#2D5A3E]/30' :
                          'text-[#1A2E22] border-[#1A2E22]/30'
                        }`}>
                          {school.bucket}
                        </span>
                      )}
                    </div>
                    {school.major_group_name && (
                      <p className="font-sans text-[13px] text-[#5A5A5A] mt-1">{school.major_group_name}</p>
                    )}
                  </div>
                </div>

                {/* Key metrics — 3 column rank data */}
                <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-white/60 rounded-none border border-[#E8E3DA]">
                  <StatBox label="考生位次" value={school.user_rank?.toLocaleString() || '—'} accent />
                  <StatBox label="参考位次" value={school.reference_rank?.toLocaleString() || '—'} />
                  <StatBox label="位次差" value={school.rank_gap != null ? (school.rank_gap > 0 ? `+${school.rank_gap}` : String(school.rank_gap)) : '—'} />
                </div>

                {/* AI Analysis — 7 labeled paragraphs */}
                {school.ai_analysis && (
                  <div className="border border-[#E8E3DA] p-6 rounded-none bg-white/50">
                    <div className="flex items-center gap-2 mb-5">
                      <Sparkles size={14} className="text-[#A8883C]" />
                      <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#A8883C]">
                        AI 院校分析
                      </span>
                    </div>

                    <AnalysisRow icon={Target} label="推荐结论" text={school.ai_analysis.recommendation_conclusion} />
                    <AnalysisRow icon={BarChart3} label="排名适配" text={school.ai_analysis.rank_fit_analysis} />
                    <AnalysisRow icon={MapPin} label="城市认知" text={school.ai_analysis.school_city_understanding} />
                    <AnalysisRow icon={Layers} label="专业组分析" text={school.ai_analysis.major_group_analysis} />
                    <AnalysisRow icon={Award} label="偏好匹配" text={school.ai_analysis.preference_match_analysis} />
                    <AnalysisRow icon={Shield} label="风险分析" text={school.ai_analysis.risk_analysis} />
                    <AnalysisRow icon={Zap} label="行动建议" text={school.ai_analysis.action_suggestion} />
                  </div>
                )}

                {/* RAG Evidence */}
                <EvidenceSection items={school.rag_evidence} />

                {/* Data Warnings */}
                <WarningSection items={school.data_warnings} />

                {/* Divider between schools */}
                {idx < school_deep_dives.length - 1 && (
                  <div className="mt-16 h-[1px] bg-gradient-to-r from-transparent via-[#A8883C]/20 to-transparent pointer-events-none" />
                )}
              </motion.div>
            ))}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 5 — 专业匹配分析 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="05" title="专业匹配分析" />

            {major_match_analysis?.major_directions && major_match_analysis.major_directions.length > 0 && (
              <div className="flex flex-wrap gap-3 mb-8">
                {major_match_analysis.major_directions.map((dir: string, i: number) => (
                  <span
                    key={i}
                    className="inline-block font-sans text-[13px] text-[#1A2E22] bg-[#1A2E22]/5 border border-[#1A2E22]/10 px-4 py-1.5 rounded-none"
                  >
                    {dir}
                  </span>
                ))}
              </div>
            )}

            {major_match_analysis?.analysis_note && (
              <div className="flex items-start gap-3 mb-6">
                <BookOpen size={16} className="text-[#A8883C] mt-1 shrink-0" />
                <p className="font-sans text-[15px] leading-[1.75] text-[#1A1A1A]">{major_match_analysis.analysis_note}</p>
              </div>
            )}

            <AiNarrativeCard text={ai_narratives?.major_match_analysis} title="专业匹配分析" />

            {major_match_analysis?.data_disclaimer && (
              <p className="font-serif text-[14px] italic leading-[1.65] text-[#8A8A8A] mt-6 text-center">
                {major_match_analysis.data_disclaimer}
              </p>
            )}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 6 — 调剂风险分析 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20 border-t border-[#E8E3DA]">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="06" title="调剂风险分析" />

            {adjustment_risk_analysis?.risk_groups && adjustment_risk_analysis.risk_groups.length > 0 ? (
              <>
                <div className="border border-[#C0392B]/20 bg-[#C0392B]/5 p-6 rounded-none mb-6">
                  <h3 className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#C0392B] flex items-center gap-2 mb-3">
                    <AlertTriangle size={14} /> 风险概览
                  </h3>
                  {adjustment_risk_analysis.risk_groups.map((group: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 mb-3 last:mb-0">
                      <span className="w-5 h-5 rounded-full bg-[#C0392B]/10 text-[#C0392B] text-[11px] flex items-center justify-center shrink-0 mt-0.5 font-medium">
                        {i + 1}
                      </span>
                      <div>
                        <p className="font-sans text-[14px] font-medium text-[#1A1A1A]">{group.name}</p>
                        <p className="font-sans text-[14px] text-[#5A5A5A]">{group.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="border border-[#2D5A3E]/20 bg-[#2D5A3E]/5 p-6 rounded-none mb-6">
                <div className="flex items-center gap-2">
                  <CheckCircle size={16} className="text-[#2D5A3E]" />
                  <p className="font-sans text-[15px] text-[#2D5A3E]">暂未发现显著的调剂风险</p>
                </div>
              </div>
            )}

            <AiNarrativeCard text={ai_narratives?.adjustment_risk_analysis} title="调剂风险分析" />

            {adjustment_risk_analysis?.summary && (
              <div className="border-l-2 border-[#A8883C] pl-4 py-2 mt-6">
                <p className="font-sans text-[14px] text-[#5A5A5A]">{adjustment_risk_analysis.summary}</p>
              </div>
            )}

            {adjustment_risk_analysis?.disclaimer && (
              <p className="font-serif text-[13px] italic text-[#8A8A8A] mt-4 text-center">
                {adjustment_risk_analysis.disclaimer}
              </p>
            )}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 7 — 地域偏好分析 (subtle)
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="07" title="地域偏好分析" />

            {region_analysis?.province_distribution && region_analysis.province_distribution.length > 0 && (
              <div className="divide-y divide-[#E8E3DA] mb-6">
                {region_analysis.province_distribution.map((item: any, i: number) => (
                  <div key={i} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <MapPin size={14} className="text-[#A8883C]" />
                      <span className="font-sans text-[15px] text-[#1A1A1A]">{item.province}</span>
                    </div>
                    <span className="font-mono text-[13px] text-[#5A5A5A]">{item.count}所</span>
                  </div>
                ))}
              </div>
            )}

            {region_analysis?.top_3_regions && region_analysis.top_3_regions.length > 0 && (
              <div className="flex flex-wrap gap-3 mb-6">
                {region_analysis.top_3_regions.map((region: string, i: number) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 font-sans text-[12px] text-[#A8883C] border border-[#A8883C]/30 px-3 py-1.5"
                  >
                    <MapPin size={12} />
                    {region}
                  </span>
                ))}
              </div>
            )}

            <AiNarrativeCard text={ai_narratives?.region_analysis} title="地域偏好分析" />
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 8 — 院校层次分析 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="08" title="院校层次分析" />

            {school_tier_analysis?.tier_distribution && school_tier_analysis.tier_distribution.length > 0 && (
              <div className="divide-y divide-[#E8E3DA] mb-6">
                {school_tier_analysis.tier_distribution.map((item: any, i: number) => (
                  <div key={i} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <GraduationCap size={14} className="text-[#A8883C]" />
                      <span className="font-sans text-[15px] text-[#1A1A1A]">{item.tier}</span>
                    </div>
                    <span className="font-mono text-[13px] text-[#5A5A5A]">{item.count}所</span>
                  </div>
                ))}
              </div>
            )}

            {school_tier_analysis?.total && (
              <p className="text-center font-sans text-[13px] text-[#8A8A8A] border-t border-[#E8E3DA] pt-4">
                共计 <span className="font-serif text-[20px] text-[#1A2E22] font-light">{school_tier_analysis.total}</span> 所院校
              </p>
            )}

            <div className="mt-6">
              <AiNarrativeCard text={ai_narratives?.school_tier_analysis} title="院校层次分析" />
            </div>
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 9 — 官方资料依据 (subtle)
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="09" title="官方资料依据" />

            {rag_evidence_sections.length > 0 ? (
              <div className="divide-y divide-[#E8E3DA]">
                {rag_evidence_sections.map((item: any, i: number) => (
                  <div key={i} className="py-4 flex items-start gap-3">
                    <BookOpen size={14} className="text-[#A8883C] mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <p className="font-sans text-[15px] text-[#1A1A1A]">{item.title || '参考资料'}</p>
                      {item.source_url && (
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-sans text-[12px] text-[#A8883C] hover:underline inline-flex items-center gap-1 mt-0.5"
                        >
                          {item.source_url} <ExternalLink size={10} />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="font-sans text-[14px] text-[#8A8A8A] italic">暂无参考资料</p>
            )}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 10 — 风险清单 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="10" title="风险清单" />

            {risk_register.length > 0 ? (
              <div className="divide-y divide-[#E8E3DA]">
                {risk_register.map((risk: any, i: number) => (
                  <div key={i} className="py-4 flex items-start gap-3">
                    {risk.severity === 'high' || risk.severity === 'critical' ? (
                      <AlertTriangle size={14} className="text-[#C0392B] shrink-0 mt-0.5" />
                    ) : risk.severity === 'medium' ? (
                      <AlertTriangle size={14} className="text-[#B8860B] shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle size={14} className="text-[#8A8A8A] shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <p className="font-sans text-[15px] text-[#1A1A1A]">{risk.risk_type}</p>
                        <span className={`font-sans text-[10px] tracking-wide uppercase px-1.5 py-0.5 ${
                          risk.severity === 'high' || risk.severity === 'critical'
                            ? 'text-[#C0392B] bg-[#C0392B]/10'
                            : risk.severity === 'medium'
                            ? 'text-[#B8860B] bg-[#B8860B]/10'
                            : 'text-[#8A8A8A] bg-[#E8E3DA]'
                        }`}>
                          {risk.severity}
                        </span>
                      </div>
                      <p className="font-sans text-[14px] text-[#5A5A5A]">{risk.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="font-sans text-[14px] text-[#8A8A8A] italic">暂无风险记录</p>
            )}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 11 — 最终建议 (subtle) — PROMINENT
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="11" title="最终建议" />

            <div className="bg-gradient-to-br from-[#A8883C]/8 to-[#1A2E22]/3 border border-[#A8883C]/15 p-10 rounded-none mb-8">
              <div className="flex items-center gap-2 mb-5">
                <Sparkles size={16} className="text-[#A8883C]" />
                <span className="font-sans text-[11px] tracking-[0.2em] uppercase font-medium text-[#A8883C]">
                  AI 最终建议
                </span>
              </div>

              {ai_narratives?.final_advice && (
                <p className="font-sans text-[16px] leading-[1.8] text-[#1A1A1A] whitespace-pre-line mb-6">
                  {ai_narratives.final_advice}
                </p>
              )}

              {/* Numbered recommendation steps */}
              {final_recommendations.length > 0 && (
                <div className="space-y-6 mt-6">
                  {final_recommendations.map((rec: any, i: number) => (
                    <div key={i} className="flex gap-4 items-start">
                      <span className="w-8 h-8 rounded-full bg-[#A8883C] text-white text-[14px] font-medium flex items-center justify-center shrink-0">
                        {i + 1}
                      </span>
                      <div>
                        <h4 className="font-sans text-[15px] font-medium text-[#1A2E22] mb-1">{rec.heading || rec.step}</h4>
                        <p className="font-sans text-[14px] leading-[1.65] text-[#5A5A5A]">{rec.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 12 — 填报前检查清单 (white)
             ============================================================ */}
        <section className="bg-white px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="12" title="填报前检查清单" />

            {/* checklist can be string[] or { label }[] */}
            {(() => {
              const items = Array.isArray(checklist)
                ? checklist.map((c: any) => (typeof c === 'string' ? c : c?.label))
                : [];
              return items.length > 0 ? (
                <div className="space-y-3">
                  {items.map((item: string, i: number) => (
                    <div key={i} className="flex items-center gap-3">
                      <CheckCircle size={16} className="text-[#2D5A3E] shrink-0" />
                      <span className="font-sans text-[15px] text-[#1A1A1A]">{item}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="font-sans text-[14px] text-[#8A8A8A] italic">暂无检查清单</p>
              );
            })()}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 13 — 数据来源 (subtle)
             ============================================================ */}
        <section className="bg-[#F8F6F1] px-8 py-20">
          <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
            <SectionHeading num="13" title="数据来源" />

            {(() => {
              // data_sources can be { name }[], { items: { name }[] }, or string
              let sources: string[] = [];
              if (data_sources) {
                if (Array.isArray(data_sources)) {
                  sources = data_sources.map((s: any) => (typeof s === 'string' ? s : s?.name));
                } else if (data_sources.items && Array.isArray(data_sources.items)) {
                  sources = data_sources.items.map((s: any) => (typeof s === 'string' ? s : s?.name));
                } else if (typeof data_sources === 'string') {
                  sources = [data_sources];
                }
              }
              return sources.length > 0 ? (
                <div className="divide-y divide-[#E8E3DA]">
                  {sources.map((name: string, i: number) => (
                    <div key={i} className="py-3 flex items-center gap-3">
                      <FileText size={14} className="text-[#A8883C] shrink-0" />
                      <span className="font-sans text-[15px] text-[#1A1A1A]">{name}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="font-sans text-[14px] text-[#8A8A8A] italic">暂无数据来源信息</p>
              );
            })()}
          </motion.div>
        </section>

        {/* ============================================================
             SECTION 14 — 免责声明 (white)
             ============================================================ */}
        {disclaimer && (
          <section className="bg-white px-8 py-20">
            <motion.div className="max-w-[760px] mx-auto" {...sectionFade}>
              <SectionHeading num="14" title="免责声明" />
              <p className="font-serif text-[15px] italic leading-[1.8] text-[#5A5A5A] text-center max-w-[560px] mx-auto text-pretty">
                {disclaimer}
              </p>
            </motion.div>
          </section>
        )}

        {/* ============================================================
             FOOTER — Dark
             ============================================================ */}
        <footer className="bg-[#1A2E22] px-8 py-14 text-center"
          style={{ WebkitPrintColorAdjust: 'exact', printColorAdjust: 'exact' } as React.CSSProperties}
        >
          <div className="max-w-[760px] mx-auto">
            <p className="font-serif text-[20px] tracking-[0.05em] text-[#A8883C] mb-3">择境 ZENPATH</p>
            <p className="font-sans text-[13px] text-white/60 mb-2">
              本报告由择境AI志愿系统自动生成 · 仅供填报参考
            </p>
            {generated_at && (
              <p className="font-mono text-[11px] text-white/30">
                报告生成时间: {formatDate(generated_at)}
              </p>
            )}
          </div>
        </footer>
      </div>
    </div>
  );
}
