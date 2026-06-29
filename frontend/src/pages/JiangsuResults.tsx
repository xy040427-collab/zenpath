import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp, Shield, AlertTriangle,
  ArrowLeft, ExternalLink, X, BookOpen, Award, Target, ChevronDown,
} from 'lucide-react';
import Button from '../components/common/Button';
import SchoolBadge from '../components/school/SchoolBadge';
import { getJiangsuRecommendations } from '../services/recommendation';
import type { JiangsuRecommendResponse, JiangsuGroupItem } from '../types';

// ═══════ Config ═══════

const BUCKET_CONFIG: Record<string, { label: string; color: string; bg: string; border: string; icon: typeof TrendingUp }> = {
  '冲': { label: '冲刺', color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-400', icon: TrendingUp },
  '稳': { label: '稳妥', color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-400', icon: Target },
  '保': { label: '保底', color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-400', icon: Shield },
  '垫': { label: '兜底', color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-400', icon: Award },
};

const RISK_COLORS: Record<string, string> = { low: 'bg-emerald-100 text-emerald-800', medium: 'bg-amber-100 text-amber-800', high: 'bg-red-100 text-red-800' };
const RISK_LABELS: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险' };
const TIER_COLORS: Record<string, string> = { '985': 'bg-purple-100 text-purple-800', '211': 'bg-blue-100 text-blue-800', '双一流': 'bg-teal-100 text-teal-800' };
const BREAKDOWN_LABELS: Record<string, string> = { rank_fit: '位次匹配', trend_stability: '趋势稳定', subject_match: '选科匹配', major_match: '专业匹配', city_match: '城市偏好', data_confidence: '数据可信' };

// ═══════ Page ═══════

export default function JiangsuResults() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as {
    score: number; rank?: number; examType: string;
    interests: string[]; regions: string[]; priority: string;
    selectedInterests?: string[]; selectedCities?: string[]; tiers?: string[];
    selectedSubjects?: string[];
  } | null;
  const [data, setData] = useState<JiangsuRecommendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeBucket, setActiveBucket] = useState('稳');
  const [detailItem, setDetailItem] = useState<JiangsuGroupItem | null>(null);

  useEffect(() => {
    if (!state?.score) { navigate('/calculator'); return; }
    const subjectType = (state.examType === '物理' || state.examType === '物理类')
      ? '物理等科目类' : '历史等科目类';
    // Use REAL selected subjects from user input, NOT hardcoded
    const selectedSubjects = state.selectedSubjects || [];
    // ✅ Use granular sub-interest selections directly (e.g. "人工智能" not "计算机/IT")
    const preferredMajors = (state.selectedInterests || []).length > 0
      ? state.selectedInterests
      : (state.interests || []).filter(Boolean);
    // ✅ Use granular city selections directly (e.g. "南京" not "长三角")
    const preferredCities = (state.selectedCities || []).length > 0
      ? state.selectedCities
      : (state.regions || []).filter(r => r !== '不限地区');
    const preferredTiers = state.tiers || [];
    const strategyMap: Record<string, string> = {
      'school': 'school_first',
      'major':  'major_first',
      'city':   'city_first',
    };
    const strategy = strategyMap[state.priority] || 'balanced';
    getJiangsuRecommendations({
      year: 2025, subject_type: subjectType, score: state.score,
      rank: state.rank,
      selected_subjects: selectedSubjects,
      preferred_majors: preferredMajors || [],
      preferred_cities: preferredCities || [],
      preferred_tiers: preferredTiers,
      strategy, top_n: 200,
    })
      .then(setData).catch(e => setError(e.message || '加载失败')).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-beige-50/30">
      <div className="text-center space-y-8">
        {/* Spinning ring */}
        <div className="relative mx-auto w-16 h-16">
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-900 border-r-brand-700"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border-2 border-transparent border-b-beige-400 border-l-beige-300"
            animate={{ rotate: -360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />
        </div>

        {/* Brand text */}
        <div className="space-y-2">
          <motion.p
            className="font-serif text-brand-900 text-base tracking-wide"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            择境 ZENPATH
          </motion.p>
          <motion.p
            className="font-sans text-beige-500 text-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            正在为你分析院校专业组…
          </motion.p>
        </div>
      </div>
    </div>
  );
  if (error || !data?.success) return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <AlertTriangle className="w-12 h-12 text-beige-400 mx-auto mb-4" />
        <h2 className="font-serif text-2xl text-brand-900 mb-2">推荐生成失败</h2>
        <p className="font-sans text-beige-600 mb-6">{error || '请检查网络连接后重试'}</p>
        <Button variant="gold" onClick={() => navigate('/calculator')}><ArrowLeft size={16} /> 返回重新填写</Button>
      </div>
    </div>
  );

  const recs = data.recommendations;
  const items: JiangsuGroupItem[] = recs[activeBucket as keyof typeof recs] || [];

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-[1600px] mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div className="text-center mb-8" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-serif text-h2 text-brand-900 mb-2">江苏志愿推荐</h1>
          <p className="font-sans text-lg font-light italic text-beige-600">
            {data.subject_type} · {data.score} 分 · 位次 {data.user_rank?.toLocaleString()}
            <span className="font-mono text-sm ml-2 text-beige-400">
              ({data.rank_source === 'user_input' ? '用户输入' : '一分一段估算'})
            </span>
          </p>
          {data.rank_warning && (
            <motion.div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 max-w-xl mx-auto text-center"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <span className="font-sans text-sm text-red-700">{data.rank_warning}</span>
            </motion.div>
          )}
          {data.rank_source === 'user_input' && data.estimated_rank_from_score && data.estimated_rank_from_score !== data.user_rank && (
            <motion.div className="mt-2 font-mono text-caption-mono text-beige-500"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
              系统按分数估算位次: {data.estimated_rank_from_score?.toLocaleString()}
            </motion.div>
          )}
        </motion.div>

        {/* Score → Rank Card */}
        <motion.div className="card-premium p-5 md:p-6 mb-6 max-w-xl mx-auto" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div className="flex items-center justify-between">
            {[
              ['你的分数', `${data.score}分`],
              ['全省位次', `${data.user_rank?.toLocaleString()}名`],
              ['科类', data.subject_type?.replace('等科目类', '')],
            ].map(([label, val]) => (
              <div key={label} className="text-center flex-1">
                <div className="font-mono text-caption-mono text-beige-500">{label}</div>
                <div className="font-serif text-2xl text-brand-900 mt-0.5">{val}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-beige-100 flex justify-around">
            {Object.entries(BUCKET_CONFIG).map(([key, cfg]) => {
              const n = (recs[key as keyof typeof recs] || []).length;
              return <div key={key} className="text-center"><div className="font-mono text-caption-mono text-beige-500">{cfg.label}</div><div className={`font-serif text-xl ${cfg.color}`}>{n}</div></div>;
            })}
          </div>
        </motion.div>

        {/* Warnings */}
        {data.warnings.length > 0 && (
          <motion.div className="max-w-5xl mx-auto mb-5 p-3 rounded-xl bg-amber-50 border border-amber-200 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            <span className="font-sans text-xs text-amber-800">{data.warnings[0]}</span>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="flex justify-center gap-2 mb-6">
          {Object.entries(BUCKET_CONFIG).map(([key, cfg]) => {
            const Icon = cfg.icon;
            const n = (recs[key as keyof typeof recs] || []).length;
            return (
              <button key={key} onClick={() => { setActiveBucket(key); setDetailItem(null); }}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-sans text-sm transition-all ${
                  activeBucket === key ? `${cfg.bg} ${cfg.color} shadow-sm font-medium` : 'bg-white text-beige-500 hover:bg-beige-50'
                }`}><Icon size={16} />{cfg.label}<span className="font-mono text-caption-mono opacity-70">({n})</span></button>
            );
          })}
        </div>

        <div className="text-center mb-6 text-beige-500 font-mono text-caption-mono">
          共 {data.summary.total_candidates} 条 · 候选池 {data.summary.candidate_pool} 组 · 去重 {data.summary.deduplicated} 条
        </div>

        {/* Card Grid — 3 columns */}
        <motion.div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 max-w-[1600px]"
          key={activeBucket} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
          {items.map((item, idx) => (
            <motion.div key={`${item.school_code}-${item.major_group_code}`}
              className={`card-premium border-l-4 ${BUCKET_CONFIG[activeBucket].border} cursor-pointer hover:shadow-md transition-shadow h-72 flex flex-col`}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.02, duration: 0.25 }}
              onClick={() => setDetailItem(item)}
            >
              <div className="p-4 flex flex-col flex-1 min-h-0">
                <div className="flex items-start gap-2.5 shrink-0">
                  <SchoolBadge slug="" name={item.school_name} size={36} className="mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <h3 className="font-serif text-sm text-brand-900 truncate">{item.school_name}</h3>
                      {item.school_tier && TIER_COLORS[item.school_tier] && <span className={`px-1 py-px rounded text-[9px] font-mono ${TIER_COLORS[item.school_tier]}`}>{item.school_tier}</span>}
                      {RISK_LABELS[item.risk_level] && <span className={`px-1 py-px rounded text-[9px] font-mono ${RISK_COLORS[item.risk_level] || ''}`}>{RISK_LABELS[item.risk_level]}</span>}
                    </div>
                    <p className="font-sans text-[11px] text-beige-600 truncate mt-0.5">{item.major_group_full_name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className={`font-serif text-lg ${BUCKET_CONFIG[activeBucket].color}`}>{item.latest_min_score}<span className="text-[10px] font-sans ml-0.5">分</span></div>
                    <div className="font-mono text-[9px] text-beige-500">{item.latest_min_rank?.toLocaleString()} 位</div>
                  </div>
                </div>

                {/* Compact stats */}
                <div className="grid grid-cols-4 gap-1.5 mt-2.5 shrink-0">
                  {[
                    ['位次差', item.rank_delta > 0 ? `+${item.rank_delta.toLocaleString()}` : item.rank_delta.toLocaleString(), item.rank_delta < 0 ? 'text-red-600' : 'text-emerald-600'],
                    ['数据', `${item.years_available}年`, 'text-brand-900'],
                    ['波动', item.rank_volatility ? `${(item.rank_volatility*100).toFixed(0)}%` : '-', item.rank_volatility && item.rank_volatility > 0.15 ? 'text-amber-600' : 'text-emerald-600'],
                    ['选科', item.subject_match_status === 'matched' ? '✅' : '⚠️', 'text-brand-900'],
                  ].map(([label, val, cls]) => (
                    <div key={label as string} className="text-center p-1 rounded bg-beige-50/70">
                      <div className={`font-mono text-[10px] font-medium ${cls}`}>{val}</div>
                      <div className="font-mono text-[8px] uppercase text-beige-500">{label}</div>
                    </div>
                  ))}
                </div>

                {/* Scrollable body — majors + reason + tags */}
                <div className="flex-1 min-h-0 mt-2 overflow-hidden relative">
                  <div className="h-full overflow-y-auto pr-1 scrollbar-none">
                    {/* ── Group majors list ── */}
                    {item.majors.length > 0 && (
                      <div className="mb-1.5">
                        <div className="flex items-center gap-1 mb-0.5">
                          <BookOpen size={9} className="text-brand-700 shrink-0" />
                          <span className="font-mono text-[8px] text-beige-500">
                            组内专业{item.group_plan_count ? `（${item.group_plan_count}人）` : ''}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-0.5">
                          {item.majors.slice(0, 6).map((m, mi) => (
                            <span key={mi} className="inline-block px-1.5 py-0.5 rounded text-[10px] font-sans bg-beige-50 text-beige-700 border border-beige-100/50">
                              {m.major_name.length > 14 ? m.major_name.slice(0, 13) + '…' : m.major_name}
                            </span>
                          ))}
                          {item.majors.length > 6 && (
                            <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono text-beige-400">+{item.majors.length - 6}</span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Reason preview */}
                    <p className="font-sans text-[11px] text-beige-600 leading-relaxed line-clamp-2">{item.reason}</p>

                    {/* Matched majors hint */}
                    {item.matched_majors.length > 0 && (
                      <div className="flex items-center gap-1 mt-1">
                        <BookOpen size={9} className="text-brand-700 shrink-0" />
                        <span className="font-sans text-[10px] text-brand-700 truncate">{item.matched_majors.map(m => m.major_name).join('、')}</span>
                      </div>
                    )}

                    {/* Risk tags */}
                    {item.risk_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {item.risk_tags.slice(0, 3).map((tag, ti) => <span key={ti} className="px-1 py-px rounded text-[9px] font-mono bg-beige-100 text-beige-600">{tag}</span>)}
                        {item.risk_tags.length > 3 && <span className="text-[9px] font-mono text-beige-400">+{item.risk_tags.length-3}</span>}
                      </div>
                    )}

                    {/* RAG evidence badge */}
                    {item.rag_evidence && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-px rounded text-[9px] font-mono ${
                          item.rag_evidence.school_profile_available && item.rag_evidence.admission_policy_available
                            ? 'bg-brand-900 text-white'
                            : item.rag_evidence.school_profile_available || item.rag_evidence.admission_policy_available
                            ? 'bg-beige-200 text-brand-800'
                            : 'bg-beige-100 text-beige-500'
                        }`}>
                          📋 {
                            item.rag_evidence.school_profile_available && item.rag_evidence.admission_policy_available
                              ? 'CHSI 官方资料'
                              : item.rag_evidence.school_profile_available
                              ? '院校简介'
                              : item.rag_evidence.admission_policy_available
                              ? '招生章程'
                              : '暂无官方资料'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                  {/* Bottom fade to hint more content in modal */}
                  <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent pointer-events-none" />
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Data note */}
        <motion.div className="max-w-5xl mx-auto mt-8 p-3 rounded-xl bg-beige-50 border border-beige-100 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <p className="font-sans text-[11px] text-beige-500">{data.data_note}</p>
        </motion.div>

        <div className="text-center mt-6">
          <Button variant="ghost" size="sm" onClick={() => navigate('/calculator')}><ArrowLeft size={14} /> 返回重新评估</Button>
        </div>
      </div>

      {/* ── Detail Modal ── */}
      <AnimatePresence>
        {detailItem && <DetailModal item={detailItem} activeBucket={activeBucket} onClose={() => setDetailItem(null)} />}
      </AnimatePresence>
    </div>
  );
}

// ═══════ Detail Modal ═══════

function DetailModal({ item, activeBucket, onClose }: { item: JiangsuGroupItem; activeBucket: string; onClose: () => void }) {
  const cfg = BUCKET_CONFIG[activeBucket];
  const [ragExpanded, setRagExpanded] = useState(false);

  return (
    <motion.div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
      {/* Card */}
      <motion.div className="relative card-premium max-w-lg w-full max-h-[85vh] overflow-y-auto"
        initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.25 }} onClick={e => e.stopPropagation()}>
        {/* Close button */}
        <button onClick={onClose} className="absolute top-3 right-3 p-1 rounded-full hover:bg-beige-100 transition-colors"><X size={18} className="text-beige-500" /></button>

        <div className="p-6">
          {/* Header */}
          <div className="flex items-start gap-3 mb-4">
            <SchoolBadge slug="" name={item.school_name} size={48} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-serif text-lg text-brand-900">{item.school_name}</h2>
                {item.school_tier && TIER_COLORS[item.school_tier] && <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${TIER_COLORS[item.school_tier]}`}>{item.school_tier}</span>}
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${RISK_COLORS[item.risk_level] || ''}`}>{RISK_LABELS[item.risk_level] || item.risk_level}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${cfg.bg} ${cfg.color}`}>{cfg.label}</span>
              </div>
              <p className="font-sans text-sm text-beige-600 mt-0.5">{item.major_group_full_name}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-mono text-[11px] text-beige-500">选科: {item.elective_requirement || '不限'} ({item.subject_match_note})</span>
              </div>
            </div>
            <div className="text-right shrink-0 ml-3">
              <div className={`font-serif text-2xl ${cfg.color}`}>{item.latest_min_score}<span className="text-sm font-sans ml-1">分</span></div>
              <div className="font-mono text-[11px] text-beige-500">位次 {item.latest_min_rank?.toLocaleString()}</div>
            </div>
          </div>

          {/* Rank details */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            {[
              ['位次差', (item.rank_delta > 0 ? '+' : '') + item.rank_delta.toLocaleString(), item.rank_delta < 0 ? 'text-red-600' : 'text-emerald-600'],
              ['ratio', `${(item.rank_delta_ratio*100).toFixed(1)}%`, 'text-brand-900'],
              ['avg位次', item.rank_avg?.toLocaleString() || '-', 'text-brand-900'],
              ['best', item.rank_best?.toLocaleString() || '-', 'text-emerald-600'],
              ['worst', item.rank_worst?.toLocaleString() || '-', 'text-red-600'],
              ['Δprev', item.rank_change_latest_vs_prev?.toLocaleString() || '-', 'text-brand-900'],
              ['波动', item.rank_volatility ? `${(item.rank_volatility*100).toFixed(1)}%` : '-', 'text-brand-900'],
              ['年份', `${item.years_available}年`, 'text-brand-900'],
            ].map(([label, val, cls]) => (
              <div key={label as string} className="text-center p-2 rounded bg-beige-50">
                <div className={`font-mono text-xs font-medium ${cls}`}>{val}</div>
                <div className="font-mono text-[9px] uppercase text-beige-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* Score breakdown */}
          {item.score_breakdown && (
            <div className="mb-4">
              <div className="font-mono text-[11px] uppercase tracking-wider text-beige-500 mb-2">综合评分: <span className="font-medium text-brand-900">{item.total_score.toFixed(3)}</span></div>
              <div className="grid grid-cols-3 gap-1.5">
                {Object.entries(item.score_breakdown).map(([k, v]) => (
                  <div key={k} className="bg-beige-50 rounded px-2 py-1.5 text-center">
                    <div className="font-mono text-[10px] text-beige-500">{BREAKDOWN_LABELS[k] || k}</div>
                    <div className="font-mono text-xs text-brand-900 font-medium">×{(v as number).toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Group majors full list ── */}
          {item.majors.length > 0 && (
            <div className="mb-4">
              <div className="font-mono text-[11px] uppercase tracking-wider text-beige-500 mb-1.5">
                组内专业清单
                {item.group_plan_count ? <span className="font-normal normal-case ml-1">（共{item.group_plan_count}人，{item.majors.length}个专业）</span> : ''}
              </div>
              <div className="grid grid-cols-2 gap-1 max-h-48 overflow-y-auto">
                {item.majors.map((m, mi) => (
                  <div key={mi} className="flex items-center justify-between bg-beige-50 rounded px-2.5 py-1.5 text-xs">
                    <span className="font-sans text-brand-900 truncate mr-1" title={m.major_name}>
                      {m.major_name.length > 28 ? m.major_name.slice(0, 27) + '…' : m.major_name}
                    </span>
                    <span className="font-mono text-[10px] text-beige-500 shrink-0">{m.plan_count}人</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Matched majors */}
          {item.matched_majors.length > 0 && (
            <div className="mb-4">
              <div className="font-mono text-[11px] uppercase tracking-wider text-beige-500 mb-1.5">专业方向匹配</div>
              <div className="space-y-1">
                {item.matched_majors.map((m, mi) => (
                  <div key={mi} className="flex items-center gap-2 text-sm bg-beige-50 rounded px-3 py-1.5">
                    <BookOpen size={14} className="text-brand-700 shrink-0" />
                    <span className="font-sans text-brand-900">{m.major_name}</span>
                    <span className="font-mono text-[10px] text-beige-500 ml-auto">
                      {m.match_type === 'exact_major_match' ? '精确匹配' :
                       m.match_type === 'category_major_match' ? '大类匹配' :
                       m.match_type === 'group_name_match' ? '名称匹配' :
                       '方向推测'} · {(m.match_score*100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk tags */}
          {item.risk_tags.length > 0 && (
            <div className="mb-4">
              <div className="font-mono text-[11px] uppercase tracking-wider text-beige-500 mb-1.5">风险标签</div>
              <div className="flex flex-wrap gap-1.5">
                {item.risk_tags.map((tag, ti) => <span key={ti} className="px-2 py-1 rounded-md text-[11px] font-mono bg-beige-100 text-beige-700">{tag}</span>)}
              </div>
            </div>
          )}

          {/* Full reason */}
          <div className="mb-4">
            <div className="font-mono text-[11px] uppercase tracking-wider text-beige-500 mb-1.5">推荐理由</div>
            <p className="font-sans text-sm text-brand-900 leading-relaxed">{item.reason}</p>
          </div>

          {/* CHSI RAG Sources */}
          {item.rag_evidence && item.rag_evidence.sources.length > 0 && (
            <div className="mb-4">
              <button
                onClick={() => setRagExpanded(!ragExpanded)}
                className="w-full flex items-center justify-between py-2 px-3 rounded-lg bg-beige-50 hover:bg-beige-100 transition-colors"
              >
                <span className="font-mono text-[11px] uppercase tracking-wider text-beige-500">
                  📋 CHSI 官方资料来源
                  <span className="normal-case ml-1 text-beige-400">（{item.rag_evidence.source_count}条）</span>
                </span>
                <motion.div
                  animate={{ rotate: ragExpanded ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronDown size={14} className="text-beige-500" />
                </motion.div>
              </button>
              <AnimatePresence initial={false}>
                {ragExpanded && (
                  <motion.div
                    className="mt-2 space-y-1.5 overflow-hidden"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {item.rag_evidence.sources.map((src, si) => (
                      <div key={si} className="flex items-center gap-2 bg-beige-50/50 rounded px-3 py-2 text-xs">
                        <span className="font-sans text-brand-900 flex-1 truncate" title={src.title}>
                          {src.title}
                        </span>
                        <a
                          href={src.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 font-mono text-[10px] text-beige-500 hover:text-brand-700 transition-colors shrink-0"
                        >
                          <ExternalLink size={10} /> 查看
                        </a>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Source */}
          <a href={item.source_url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-mono text-[11px] text-beige-500 hover:text-brand-700 transition-colors">
            <ExternalLink size={11} /> 数据来源: 江苏省教育考试院 (jseea.cn)
          </a>
        </div>
      </motion.div>
    </motion.div>
  );
}
