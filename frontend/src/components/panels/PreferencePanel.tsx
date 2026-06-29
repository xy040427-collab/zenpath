import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Building2,
  GraduationCap,
  Award,
  University,
  BookOpen,
  Check,
  MapPin,
  Heart,
} from 'lucide-react';

/* ──────────────────────────────────────────
   Data Constants (inline)
   ────────────────────────────────────────── */

const INTEREST_CATEGORIES: Record<string, string[]> = {
  '计算机/IT': ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '网络安全', '物联网工程', '数字媒体技术'],
  '医学/药学': ['临床医学', '口腔医学', '药学', '中医学', '护理学', '医学影像学', '预防医学'],
  '金融/经济': ['金融学', '经济学', '会计学', '国际经济与贸易', '财政学', '保险学', '投资学'],
  '法学/政治': ['法学', '知识产权', '政治学', '社会学', '国际政治', '行政管理'],
  '教育/师范': ['教育学', '汉语言文学(师范)', '数学(师范)', '英语(师范)', '小学教育', '学前教育'],
  '工程/制造': ['机械工程', '电气工程', '自动化', '土木工程', '建筑学', '材料科学', '车辆工程'],
  '传媒/艺术': ['新闻学', '广告学', '广播电视学', '设计学', '美术学', '音乐学', '戏剧影视'],
  '农林/环境': ['农学', '林学', '环境工程', '食品科学', '生物技术', '生态学'],
  '语言/文学': ['汉语言文学', '英语', '日语', '法语', '翻译', '历史学', '哲学'],
  '管理/商科': ['工商管理', '市场营销', '人力资源管理', '物流管理', '电子商务', '旅游管理'],
};

const REGIONS: Record<string, { cities: string[]; emoji: string }> = {
  '长三角': { cities: ['南京', '苏州', '无锡', '杭州', '上海', '宁波', '常州', '镇江', '扬州', '南通'], emoji: '🏙️' },
  '京津冀': { cities: ['北京', '天津', '石家庄', '保定', '唐山'], emoji: '🏛️' },
  '珠三角': { cities: ['广州', '深圳', '珠海', '佛山', '东莞', '中山'], emoji: '🌆' },
  '华中地区': { cities: ['武汉', '长沙', '郑州', '南昌', '合肥'], emoji: '🏗️' },
  '西南地区': { cities: ['成都', '重庆', '昆明', '贵阳'], emoji: '🌄' },
  '西北地区': { cities: ['西安', '兰州', '乌鲁木齐'], emoji: '🏔️' },
  '东北地区': { cities: ['哈尔滨', '长春', '沈阳', '大连'], emoji: '❄️' },
};

const TIERS = ['985', '211', '双一流', '省重点', '公办本科'] as const;

const TIER_COLORS: Record<string, string> = {
  '985': 'bg-amber-50 text-amber-700 border-amber-200',
  '211': 'bg-sky-50 text-sky-700 border-sky-200',
  '双一流': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  '省重点': 'bg-violet-50 text-violet-700 border-violet-200',
  '公办本科': 'bg-slate-50 text-slate-600 border-slate-200',
};

const TIER_ICONS: Record<string, React.ReactNode> = {
  '985': <Building2 size={18} />,
  '211': <GraduationCap size={18} />,
  '双一流': <Award size={18} />,
  '省重点': <University size={18} />,
  '公办本科': <BookOpen size={18} />,
};

/* ──────────────────────────────────────────
   Types
   ────────────────────────────────────────── */

interface PreferencePanelProps {
  interests: string[];
  selectedInterests: string[];
  onToggleSubInterest: (sub: string) => void;
  onToggleInterestCategory: (category: string) => void;

  regions: string[];
  selectedCities: string[];
  onToggleCity: (city: string) => void;
  onToggleRegion: (region: string) => void;

  tiers: string[];
  onToggleTier: (tier: string) => void;
}

/* ──────────────────────────────────────────
   Sub-components
   ────────────────────────────────────────── */

function Chip({
  selected,
  label,
  onClick,
  showCheck,
  pulseKey,
  variant = 'interest',
}: {
  selected: boolean;
  label: string;
  onClick: () => void;
  showCheck?: boolean;
  pulseKey?: string;
  variant?: 'interest' | 'city';
}) {
  const base =
    'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm cursor-pointer select-none transition-colors duration-200';

  const interestClasses = selected
    ? 'bg-brand-900 text-white'
    : 'bg-beige-100 text-beige-600 hover:bg-beige-200';

  const cityClasses = selected
    ? 'bg-brand-900 text-white'
    : 'bg-beige-100 text-beige-500 hover:bg-beige-200';

  const classes = variant === 'city' ? cityClasses : interestClasses;

  return (
    <motion.span
      key={pulseKey}
      className={`${base} ${classes}`}
      onClick={onClick}
      initial={false}
      animate={pulseKey ? { scale: [1, 1.05, 1] } : {}}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      layout
    >
      {selected && showCheck && <Check size={13} strokeWidth={3} />}
      {label}
    </motion.span>
  );
}

function TierBadge({
  tier,
  selected,
  onClick,
  pulseKey,
}: {
  tier: string;
  selected: boolean;
  onClick: () => void;
  pulseKey?: string;
}) {
  return (
    <motion.button
      key={pulseKey}
      onClick={onClick}
      initial={false}
      animate={
        pulseKey
          ? { scale: [1, 1.05, 1] }
          : selected
            ? { scale: 1.05 }
            : { scale: 1 }
      }
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className={`
        relative flex items-center gap-2.5 rounded-xl border px-4 py-3 text-sm font-medium
        transition-all duration-200 cursor-pointer
        ${TIER_COLORS[tier] || 'bg-beige-50 text-beige-600 border-beige-200'}
        ${
          selected
            ? 'ring-2 ring-brand-900/30 shadow-md'
            : 'opacity-60 hover:opacity-85'
        }
      `}
    >
      <span className="shrink-0">{TIER_ICONS[tier]}</span>
      <span>{tier}</span>
    </motion.button>
  );
}

/* ──────────────────────────────────────────
   Main Component
   ────────────────────────────────────────── */

export default function PreferencePanel({
  interests,
  selectedInterests,
  onToggleSubInterest,
  regions,
  selectedCities,
  onToggleCity,
  tiers,
  onToggleTier,
  ..._unused
}: PreferencePanelProps) {
  void _unused; // onToggleInterestCategory, onToggleRegion reserved
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [activeRegion, setActiveRegion] = useState<string | null>(null);
  const [animKey, setAnimKey] = useState(0);

  // Derived: all sub-interests (flattened)
  const allSubInterests = Object.values(INTEREST_CATEGORIES).flat();

  // Filtered sub-interests based on active category
  const displayedSubInterests = activeCategory
    ? INTEREST_CATEGORIES[activeCategory] ?? []
    : allSubInterests;

  // Filtered cities based on active region
  const displayedCities = activeRegion
    ? REGIONS[activeRegion]?.cities ?? []
    : Object.values(REGIONS).flatMap((r) => r.cities);

  // Count selected sub-interests per category
  const selectedCountInCategory = (cat: string) =>
    INTEREST_CATEGORIES[cat].filter((s) => selectedInterests.includes(s)).length;

  // Check if a region is fully selected
  const isRegionFullySelected = (region: string) => {
    const cities = REGIONS[region]?.cities ?? [];
    return cities.length > 0 && cities.every((c) => selectedCities.includes(c));
  };

  // Trigger pulse animation
  const triggerPulse = useCallback(() => {
    setAnimKey((k) => k + 1);
  }, []);

  const handleInterestCategoryClick = (cat: string) => {
    if (activeCategory === cat) {
      setActiveCategory(null);
    } else {
      setActiveCategory(cat);
    }
  };

  const handleRegionClick = (region: string) => {
    if (activeRegion === region) {
      setActiveRegion(null);
    } else {
      setActiveRegion(region);
    }
  };

  const handleSelectAllRegion = () => {
    if (!activeRegion) return;
    const cities = REGIONS[activeRegion]?.cities ?? [];
    const allSelected = cities.every((c) => selectedCities.includes(c));
    if (allSelected) {
      cities.forEach((c) => {
        if (selectedCities.includes(c)) onToggleCity(c);
      });
    } else {
      cities.forEach((c) => {
        if (!selectedCities.includes(c)) onToggleCity(c);
      });
    }
    triggerPulse();
  };

  const handleTierClick = (tier: string) => {
    onToggleTier(tier);
    triggerPulse();
  };

  const handleSubInterestClick = (sub: string) => {
    onToggleSubInterest(sub);
    triggerPulse();
  };

  const handleCityClick = (city: string) => {
    onToggleCity(city);
    triggerPulse();
  };

  return (
    <div className="rounded-2xl border border-beige-200/50 bg-white/60 backdrop-blur-sm p-5">
      {/* ── Three-column grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0">
        {/* ================================================================ */}
        {/* Column 1 — 兴趣方向 */}
        {/* ================================================================ */}
        <div className="border-r-0 md:border-r border-beige-100 px-0 md:px-5 first:pl-0 last:pr-0 pb-5 md:pb-0">
          {/* Header */}
          <h3 className="font-serif text-brand-900 text-base font-semibold mb-3 flex items-center gap-2">
            <Heart size={16} className="text-gold" />
            兴趣方向
            {selectedInterests.length > 0 && (
              <span className="ml-auto text-xs font-sans font-normal text-beige-500">
                已选 {selectedInterests.length}
              </span>
            )}
          </h3>

          {/* Category tabs — horizontal scroll */}
          <div className="flex flex-wrap gap-1.5 mb-3 max-h-[3.5rem] overflow-y-auto">
            {interests.length === 0 ? (
              Object.keys(INTEREST_CATEGORIES).map((cat) => {
                const count = selectedCountInCategory(cat);
                const isActive = activeCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => handleInterestCategoryClick(cat)}
                    className={`
                      inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap
                      transition-colors duration-200 cursor-pointer shrink-0
                      ${
                        isActive
                          ? 'bg-brand-900 text-white'
                          : 'bg-beige-100 text-beige-600 hover:bg-beige-200'
                      }
                    `}
                  >
                    {cat}
                    {count > 0 && (
                      <span
                        className={`
                          inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full text-[10px] font-bold
                          ${isActive ? 'bg-white/20 text-white' : 'bg-brand-900/10 text-brand-900'}
                        `}
                      >
                        {count}
                      </span>
                    )}
                  </button>
                );
              })
            ) : (
              interests.map((cat) => {
                const count = selectedCountInCategory(cat);
                const isActive = activeCategory === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => handleInterestCategoryClick(cat)}
                    className={`
                      inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap
                      transition-colors duration-200 cursor-pointer shrink-0
                      ${
                        isActive
                          ? 'bg-brand-900 text-white'
                          : 'bg-beige-100 text-beige-600 hover:bg-beige-200'
                      }
                    `}
                  >
                    {cat}
                    {count > 0 && (
                      <span
                        className={`
                          inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full text-[10px] font-bold
                          ${isActive ? 'bg-white/20 text-white' : 'bg-brand-900/10 text-brand-900'}
                        `}
                      >
                        {count}
                      </span>
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Sub-interest chips */}
          <div className="flex flex-wrap gap-2">
            {displayedSubInterests.length === 0 && (
              <p className="text-beige-400 text-sm py-2">选择偏好方向</p>
            )}
            {displayedSubInterests.map((sub) => (
              <Chip
                key={sub}
                label={sub}
                selected={selectedInterests.includes(sub)}
                onClick={() => handleSubInterestClick(sub)}
                showCheck
                pulseKey={selectedInterests.includes(sub) ? `${sub}-${animKey}` : undefined}
              />
            ))}
          </div>
        </div>

        {/* ================================================================ */}
        {/* Column 2 — 目标地区 */}
        {/* ================================================================ */}
        <div className="border-r-0 md:border-r border-beige-100 px-0 md:px-5 first:pl-0 last:pr-0 pb-5 md:pb-0">
          {/* Header */}
          <h3 className="font-serif text-brand-900 text-base font-semibold mb-3 flex items-center gap-2">
            <MapPin size={16} className="text-gold" />
            目标地区
            {selectedCities.length > 0 && (
              <span className="ml-auto text-xs font-sans font-normal text-beige-500">
                已选 {selectedCities.length}
              </span>
            )}
          </h3>

          {/* Region tabs — horizontal scroll with emoji */}
          <div className="flex flex-wrap gap-1.5 mb-3 max-h-[3.5rem] overflow-y-auto">
            {regions.length === 0
              ? Object.entries(REGIONS).map(([region, data]) => {
                  const isActive = activeRegion === region;
                  const fullySelected = isRegionFullySelected(region);
                  return (
                    <button
                      key={region}
                      onClick={() => handleRegionClick(region)}
                      className={`
                        inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap
                        transition-colors duration-200 cursor-pointer shrink-0
                        ${
                          isActive
                            ? 'bg-brand-900 text-white'
                            : 'bg-beige-100 text-beige-600 hover:bg-beige-200'
                        }
                      `}
                    >
                      <span className="text-sm leading-none">{data.emoji}</span>
                      <span>{region}</span>
                      {fullySelected && (
                        <Check size={11} strokeWidth={3} className="text-white" />
                      )}
                    </button>
                  );
                })
              : Object.entries(REGIONS)
                  .filter(([region]) => regions.includes(region))
                  .map(([region, data]) => {
                    const isActive = activeRegion === region;
                    const fullySelected = isRegionFullySelected(region);
                    return (
                      <button
                        key={region}
                        onClick={() => handleRegionClick(region)}
                        className={`
                          inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap
                          transition-colors duration-200 cursor-pointer shrink-0
                          ${
                            isActive
                              ? 'bg-brand-900 text-white'
                              : 'bg-beige-100 text-beige-600 hover:bg-beige-200'
                          }
                        `}
                      >
                        <span className="text-sm leading-none">{data.emoji}</span>
                        <span>{region}</span>
                        {fullySelected && (
                          <Check size={11} strokeWidth={3} className="text-white" />
                        )}
                      </button>
                    );
                  })}
          </div>

          {/* Quick-select button (only when a specific region is active) */}
          {activeRegion && (
            <button
              onClick={handleSelectAllRegion}
              className="mb-2.5 text-xs text-brand-800 font-medium flex items-center gap-1 hover:text-brand-900 transition-colors cursor-pointer"
            >
              <span className="inline-flex items-center justify-center w-4 h-4 rounded bg-brand-800/10">
                <Check size={10} className="text-brand-800" />
              </span>
              全选区域
              {isRegionFullySelected(activeRegion) ? ' (取消)' : ''}
            </button>
          )}

          {/* City chips */}
          <div className="flex flex-wrap gap-2">
            {displayedCities.length === 0 && (
              <p className="text-beige-400 text-sm py-2">选择目标城市</p>
            )}
            {displayedCities.map((city) => {
              const isSelected = selectedCities.includes(city);
              return (
                <Chip
                  key={city}
                  label={city}
                  selected={isSelected}
                  onClick={() => handleCityClick(city)}
                  showCheck
                  pulseKey={isSelected ? `${city}-${animKey}` : undefined}
                  variant="city"
                />
              );
            })}
          </div>
        </div>

        {/* ================================================================ */}
        {/* Column 3 — 学校层次 */}
        {/* ================================================================ */}
        <div className="px-0 md:px-5 first:pl-0 last:pr-0">
          {/* Header */}
          <h3 className="font-serif text-brand-900 text-base font-semibold mb-3 flex items-center gap-2">
            <Award size={16} className="text-gold" />
            学校层次
            {tiers.length > 0 && (
              <span className="ml-auto text-xs font-sans font-normal text-beige-500">
                已选 {tiers.length}
              </span>
            )}
          </h3>

          {/* Tier badges grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {TIERS.map((tier) => (
              <TierBadge
                key={tier}
                tier={tier}
                selected={tiers.includes(tier)}
                onClick={() => handleTierClick(tier)}
                pulseKey={tiers.includes(tier) ? `${tier}-${animKey}` : undefined}
              />
            ))}
          </div>

          {tiers.length === 0 && (
            <p className="text-beige-400 text-sm py-2">选择学校层次</p>
          )}
        </div>
      </div>
    </div>
  );
}
