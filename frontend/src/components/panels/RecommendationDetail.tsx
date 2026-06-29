import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, Shield, BookOpen, Briefcase, AlertTriangle, Database, ExternalLink, GraduationCap } from 'lucide-react';
import type { VolunteerItem } from '../../types';

interface RecommendationDetailProps {
  item: VolunteerItem;
  onClose: () => void;
  dataCoverage?: { score_rank: string; admission_lines: string; rag_knowledge: string; warnings: string[] };
}

export default function RecommendationDetail({ item, onClose, dataCoverage }: RecommendationDetailProps) {
  const ai = item.ai_explanation;
  const summary = item.recommendation_summary || item.rag_summary || '';

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-start justify-center pt-16 pb-8 px-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

        {/* Panel */}
        <motion.div
          className="relative w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.25 }}
        >
          {/* Close button */}
          <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-full hover:bg-stone-100 transition-colors z-10">
            <X size={20} className="text-stone-400" />
          </button>

          <div className="p-6 md:p-8">
            {/* Header */}
            <div className="mb-6">
              <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium mb-3 ${
                item.tier === '冲刺' ? 'bg-amber-100 text-amber-700' :
                item.tier === '稳妥' ? 'bg-emerald-100 text-emerald-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {item.tier === '冲刺' ? '⚠️ 冲刺' : item.tier === '稳妥' ? '✅ 稳妥' : '🎯 保底'}
              </span>
              <h2 className="font-serif text-2xl text-brand-900">{item.schoolName}</h2>
              <p className="text-stone-500 mt-1 flex items-center gap-1">
                <GraduationCap size={16} />
                {item.majorName}
              </p>
            </div>

            {/* 录取数据 */}
            <Section icon={<Database size={18} />} title="录取数据">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <DataItem label="最新最低分" value={item.minScore ? `${item.minScore}分` : '—'} />
                <DataItem label="最新最低位次" value={item.minRank ? `${item.minRank}名` : '—'} />
                <DataItem label="近3年均位" value={item.avgRank ? `${item.avgRank}名` : '—'} />
                <DataItem label="招生计划" value={item.plan_count ? `${item.plan_count}人` : '—'} />
              </div>
            </Section>

            {/* 为什么是冲/稳/保 */}
            <Section icon={<Shield size={18} />} title={`为什么是${item.tier}？`}>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl font-bold text-brand-900">{Math.round(item.probability * 100)}%</span>
                <span className="text-sm text-stone-500">录取概率</span>
              </div>
              <p className="text-sm text-stone-600 leading-relaxed">{item.reason}</p>
              <p className="text-sm text-stone-500 mt-2">匹配度: {item.matchScore}%</p>
            </Section>

            {/* 学校分析 */}
            {ai?.school_analysis && (
              <Section icon={<BookOpen size={18} />} title="学校分析">
                <p className="text-sm text-stone-600 leading-relaxed">{ai.school_analysis}</p>
              </Section>
            )}
            {!ai?.school_analysis && summary && (
              <Section icon={<BookOpen size={18} />} title="学校概况">
                <div className="text-sm text-stone-600 leading-relaxed whitespace-pre-line"
                  dangerouslySetInnerHTML={{ __html: summary.replace(/\n/g, '<br/>') }} />
              </Section>
            )}

            {/* 专业分析 */}
            {ai?.major_analysis && (
              <Section icon={<BookOpen size={18} />} title="专业分析">
                <p className="text-sm text-stone-600 leading-relaxed">{ai.major_analysis}</p>
              </Section>
            )}

            {/* 职业路径 */}
            {ai?.career_path && (
              <Section icon={<Briefcase size={18} />} title="职业路径">
                <p className="text-sm text-stone-600 leading-relaxed">{ai.career_path}</p>
              </Section>
            )}

            {/* 风险提示 */}
            {ai?.risk_warning && (
              <Section icon={<AlertTriangle size={18} />} title="风险提示" className="bg-amber-50 border-amber-200">
                <p className="text-sm text-amber-800 leading-relaxed">{ai.risk_warning}</p>
              </Section>
            )}

            {/* 数据覆盖 */}
            {dataCoverage && (
              <Section icon={<Database size={18} />} title="数据覆盖状态">
                <div className="flex flex-wrap gap-2">
                  <Pill label="一分一段表" status={dataCoverage.score_rank} />
                  <Pill label="投档线" status={dataCoverage.admission_lines} />
                  <Pill label="RAG知识库" status={dataCoverage.rag_knowledge} />
                </div>
                {dataCoverage.warnings?.map((w: string, i: number) => (
                  <p key={i} className="text-xs text-amber-600 mt-2">⚠️ {w}</p>
                ))}
              </Section>
            )}

            {/* 资料来源 */}
            {ai?.sources && ai.sources.length > 0 && (
              <Section icon={<ExternalLink size={18} />} title="资料来源">
                <div className="space-y-1">
                  {ai.sources.map((s: {source_name: string; source_url: string}, i: number) => (
                    <a key={i} href={s.source_url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                      <ExternalLink size={12} /> {s.source_name}
                    </a>
                  ))}
                </div>
              </Section>
            )}

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-cream-200 flex justify-end">
              <button onClick={onClose}
                className="px-5 py-2 bg-brand-900 text-white rounded-lg text-sm hover:bg-brand-800 transition-colors">
                关闭
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function Section({ icon, title, children, className = '' }: {
  icon: React.ReactNode; title: string; children: React.ReactNode; className?: string;
}) {
  return (
    <div className={`mb-4 p-5 rounded-xl border border-cream-200 bg-cream-50 ${className}`}>
      <h3 className="font-serif text-lg text-brand-900 mb-3 flex items-center gap-2">
        {icon} {title}
      </h3>
      {children}
    </div>
  );
}

function DataItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg p-3 border border-cream-200">
      <p className="text-xs text-stone-400 mb-1">{label}</p>
      <p className="text-sm font-medium text-stone-800">{value}</p>
    </div>
  );
}

function Pill({ label, status }: { label: string; status: string }) {
  const colors = {
    available: 'bg-emerald-100 text-emerald-700',
    partial: 'bg-amber-100 text-amber-700',
    missing: 'bg-red-100 text-red-700',
  };
  const labels: Record<string, string> = {
    available: '✅', partial: '⚠️', missing: '❌',
  };
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${colors[status as keyof typeof colors] || 'bg-stone-100 text-stone-500'}`}>
      {labels[status] || ''} {label}
    </span>
  );
}
