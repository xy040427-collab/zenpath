import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, TrendingUp, Loader2, Building2, BookOpen } from 'lucide-react';
import Button from '../components/common/Button';
import ScoreBadge from '../components/common/ScoreBadge';
import { getRecommendations } from '../services/recommendation';
import type { VolunteerItem } from '../types';
import { formatProbability, formatRank } from '../utils/formatters';
import { TIER_COLORS } from '../utils/constants';
import QuickTips from '../components/panels/QuickTips';
import RelatedLinks from '../components/panels/RelatedLinks';
import DataCoverageBanner from '../components/panels/DataCoverageBanner';
import RecommendationDetail from '../components/panels/RecommendationDetail';

/* ── Expandable Card ── */

function ExpandableCard({ item, index, onViewDetail }: { item: VolunteerItem; index: number; onViewDetail: (item: VolunteerItem) => void }) {
  const tierColor = TIER_COLORS[item.tier];
  const rag = (item as any).rag_summary as string | undefined;

  return (
    <motion.div
      className="card-premium p-5 sm:p-6 flex flex-col"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
    >
      {/* Tier badge + logo */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {item.schoolLogo ? (
            <img
              src={`/urongda-logos/${item.schoolLogo}_logo_128.png`}
              alt={item.schoolName}
              className="w-9 h-9 rounded-lg object-contain bg-white shrink-0"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          ) : (
            <div className="w-9 h-9 rounded-lg bg-brand-900/10 flex items-center justify-center shrink-0">
              <span className="font-serif text-xs text-brand-900">{item.schoolName.slice(0, 2)}</span>
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h4 className="font-serif text-lg font-normal text-brand-900 truncate">{item.schoolName}</h4>
            </div>
            <div className="flex items-center gap-1.5">
              <BookOpen size={12} className="text-beige-500 shrink-0" />
              <span className="font-sans text-sm font-light text-ink truncate">{item.majorName}</span>
            </div>
          </div>
        </div>
        <span className={`shrink-0 text-[10px] font-mono uppercase tracking-[0.15em] px-3 py-1 rounded-full ${tierColor.bg} ${tierColor.text}`}>
          {item.tier}
        </span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{formatProbability(item.probability)}</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">录取率</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{formatRank(item.expectedRank)}</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">位次</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{item.matchScore}%</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">匹配</div>
        </div>
      </div>

      {/* Reason */}
      {item.reason && (
        <div className="flex items-start gap-2 mt-auto pt-3 border-t border-stone">
          <TrendingUp size={13} className="text-accent-gold mt-0.5 shrink-0" />
          <p className="font-sans text-xs font-light text-beige-700 leading-relaxed">{item.reason}</p>
        </div>
      )}

      {/* View detail button */}
      {rag && (
        <button
          onClick={() => onViewDetail(item)}
          className="flex items-center gap-1.5 mt-3 text-xs text-beige-500 hover:text-accent-gold transition-colors w-fit"
        >
          <BookOpen size={14} />
          查看详情
        </button>
      )}
    </motion.div>
  );
}

/* ── Collapsible Section ── */

function RiskSection({
  title, subtitle, color, items, defaultOpen, onViewDetail,
}: {
  title: string; subtitle: string; color: string; items: VolunteerItem[]; defaultOpen: boolean;
  onViewDetail: (item: VolunteerItem) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="mb-8">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 mb-4 w-full text-left hover:opacity-80 transition-opacity"
      >
        <div className={`w-3 h-3 rounded-full ${color}`} />
        <h2 className="font-serif text-2xl font-normal text-brand-900">{title}</h2>
        <span className="font-mono text-caption-mono opacity-60">{subtitle}</span>
        <span className="font-mono text-xs text-beige-500 ml-auto">{items.length}所</span>
        {open ? <ChevronUp size={18} className="text-beige-500" /> : <ChevronDown size={18} className="text-beige-500" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {items.map((item, i) => (
                <ExpandableCard key={item.id} item={item} index={i} onViewDetail={onViewDetail} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ── Main Preview Page ── */

export default function Preview() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = location.state as {
    score: number; rank: number; province: string; examType: string;
    interests?: string[]; regions?: string[]; priority?: string;
  } | null;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rush, setRush] = useState<VolunteerItem[]>([]);
  const [stable, setStable] = useState<VolunteerItem[]>([]);
  const [safe, setSafe] = useState<VolunteerItem[]>([]);
  const [summary, setSummary] = useState<Record<string, unknown>>({});
  const [dataCoverage, setDataCoverage] = useState<{ score_rank: string; admission_lines: string; rag_knowledge: string; warnings: string[] } | null>(null);
  const [selectedItem, setSelectedItem] = useState<VolunteerItem | null>(null);

  useEffect(() => {
    if (!params) return;
    setLoading(true);
    getRecommendations({
      score: params.score, rank: params.rank, province: params.province, examType: params.examType,
      interests: params.interests, regions: params.regions, priority: params.priority,
    })
      .then((result) => { setRush(result.rush); setStable(result.stable); setSafe(result.safe); setSummary(result.summary); setDataCoverage((result.summary as any).data_coverage || null); })
      .catch((err) => { setError(err instanceof Error ? err.message : '获取推荐失败'); })
      .finally(() => setLoading(false));
  }, [params]);

  if (!params) { navigate('/calculator'); return null; }

  if (loading) {
    return (
      <div className="min-h-screen pt-28 md:pt-32 pb-20 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-brand-900 mx-auto mb-4" />
          <p className="font-sans text-sm font-light text-beige-600">正在分析你的志愿方案...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen pt-28 md:pt-32 pb-20 flex items-center justify-center">
        <div className="text-center">
          <p className="font-sans text-sm font-light text-[#A84A3A] mb-4">分析失败：{error}</p>
          <Button variant="outline" onClick={() => navigate('/calculator')}>重新填写</Button>
        </div>
      </div>
    );
  }

  const total = rush.length + stable.length + safe.length;
  const matchRate = (summary.match_rate ?? 85) as number;
  const totalCandidates = Number(summary.total_candidates ?? total) || 0;

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div className="text-center mb-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="font-serif text-h2 text-brand-900 mb-3">你的志愿方案</h1>
          <p className="font-sans text-lg font-light italic text-beige-600 mb-8">
            基于{params.province} {params.examType}类 {params.score}分 · 位次 {params.rank.toLocaleString()}
          </p>
          <ScoreBadge score={params.score} rank={params.rank} />
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1 min-w-0">
            {/* Data Coverage Banner */}
            {dataCoverage && <DataCoverageBanner coverage={dataCoverage} />}

            {/* Summary */}
            <motion.div className="card-premium p-8 md:p-10 mb-10" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.6 }}>
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="text-center flex-1">
                  <div className="font-serif text-4xl font-light text-brand-900">{matchRate}%</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-1">综合匹配度</div>
                </div>
                <div className="w-px h-16 bg-[#E0D8CC] hidden md:block" />
                <div className="text-center flex-1">
                  <div className="font-serif text-4xl font-light text-brand-900">{totalCandidates}</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-1">可报院校</div>
                </div>
                <div className="w-px h-16 bg-[#E0D8CC] hidden md:block" />
                <div className="text-center flex-1">
                  <div className="flex items-center justify-center gap-3 text-center">
                    <div><div className="font-mono text-xs font-medium text-[#A84A3A]">{rush.length}</div><div className="font-mono text-[9px] uppercase tracking-[0.1em] text-beige-500">冲刺</div></div>
                    <div className="w-px h-8 bg-[#E0D8CC]" />
                    <div><div className="font-mono text-xs font-medium text-[#C4A45C]">{stable.length}</div><div className="font-mono text-[9px] uppercase tracking-[0.1em] text-beige-500">稳妥</div></div>
                    <div className="w-px h-8 bg-[#E0D8CC]" />
                    <div><div className="font-mono text-xs font-medium text-[#4A8A7A]">{safe.length}</div><div className="font-mono text-[9px] uppercase tracking-[0.1em] text-beige-500">保底</div></div>
                  </div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-2">冲稳保分布</div>
                </div>
              </div>
            </motion.div>

            {/* Warnings */}
            {(summary.warnings as string[])?.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 mb-8">
                {(summary.warnings as string[]).map((w, i) => (
                  <p key={i} className="text-sm text-amber-800">{w}</p>
                ))}
              </div>
            )}

            {/* Sections */}
            {rush.length > 0 && <RiskSection title="冲刺院校" subtitle="需前进15%+" color="bg-[#A84A3A]" items={rush} defaultOpen={false} onViewDetail={setSelectedItem} />}
            {stable.length > 0 && <RiskSection title="稳妥院校" subtitle="位次匹配" color="bg-[#C4A45C]" items={stable} defaultOpen={true} onViewDetail={setSelectedItem} />}
            {safe.length > 0 && <RiskSection title="保底院校" subtitle="领先15%+" color="bg-[#4A8A7A]" items={safe} defaultOpen={false} onViewDetail={setSelectedItem} />}

            {/* Detail Modal */}
            {selectedItem && (
              <RecommendationDetail
                item={selectedItem}
                onClose={() => setSelectedItem(null)}
                dataCoverage={dataCoverage || undefined}
              />
            )}

            {/* Actions */}
            <motion.div className="flex flex-wrap items-center justify-center gap-4 mt-10" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
              <Button variant="gold" size="lg" onClick={() => navigate('/volunteer-list')}>浏览完整院校列表</Button>
              <Button variant="outline" size="lg" onClick={() => navigate('/chat', { state: { ...params, summary } })}>AI 深度对话</Button>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="hidden lg:flex flex-col gap-6 w-80 shrink-0">
            <div className="sticky top-32 space-y-6">
              <QuickTips />
              <RelatedLinks />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
