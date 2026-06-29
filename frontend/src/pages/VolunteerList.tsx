import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, MapPin, ChevronLeft, ChevronRight } from 'lucide-react';
import Badge from '../components/common/Badge';
import SchoolBadge from '../components/school/SchoolBadge';
import { fetchSchools, fetchSchoolsMeta, type SchoolData } from '../services/school';
import StatsSidebar from '../components/panels/StatsSidebar';
import QuickTips from '../components/panels/QuickTips';
import RelatedLinks from '../components/panels/RelatedLinks';

// ========== Filter Options ==========

const LEVEL_FILTERS = ['全部', '985', '211', '双一流', '普通'];
const TYPE_FILTERS = ['全部', '综合', '理工', '师范', '医药', '农林', '政法', '财经', '艺术', '体育'];

const ITEMS_PER_PAGE = 25;

// ========== Helpers ==========

function getLevelBadgeVariant(level: string): 'ruby' | 'gold' | 'teal' | 'outline' {
  if (level === '985') return 'ruby';
  if (level === '211') return 'gold';
  if (level === '双一流') return 'teal';
  return 'outline';
}

// ========== Counter Hook ==========
function useCountUp(target: number, duration: number = 2, start: boolean = true) {
  const [count, setCount] = useState(0);
  const frameRef = useRef<number>();
  const startedRef = useRef(false);

  useEffect(() => {
    if (!start) return;
    // Reset and re-animate whenever target changes
    cancelAnimationFrame(frameRef.current!);
    setCount(0);
    startedRef.current = false;

    if (target === 0) return;
    startedRef.current = true;
    let frame: number;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = (now - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCount(Math.round(eased * target));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [target, duration, start]);

  return count;
}

// ========== Component ==========

export default function VolunteerList() {
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('全部');
  const [typeFilter, setTypeFilter] = useState('全部');
  const [provinceFilter, setProvinceFilter] = useState('全部');
  const [currentPage, setCurrentPage] = useState(1);

  // API state
  const [schools, setSchools] = useState<SchoolData[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [provinces, setProvinces] = useState<string[]>(['全部']);

  // Meta counts from API (real data)
  const [metaLevelCounts, setMetaLevelCounts] = useState<Record<string, number>>({});
  const [metaProvinceCounts, setMetaProvinceCounts] = useState<Record<string, number>>({});
  const [metaTotal, setMetaTotal] = useState(863); // default to known total
  const [metaProvinceCount, setMetaProvinceCount] = useState(31);

  // Fetch meta on mount
  useEffect(() => {
    fetchSchoolsMeta()
      .then((meta) => {
        setProvinces(['全部', ...meta.provinces]);
        setMetaLevelCounts(meta.level_counts || {});
        setMetaProvinceCounts(meta.province_counts || {});
        setMetaTotal(meta.total);
        setMetaProvinceCount(meta.provinces?.length || 0);
      })
      .catch(() => {
        // fallback to empty
      });
  }, []);

  // Fetch schools when filters or page change
  useEffect(() => {
    setLoading(true);
    fetchSchools({
      page: currentPage,
      page_size: ITEMS_PER_PAGE,
      search: search || undefined,
      level: levelFilter === '全部' ? undefined : levelFilter,
      type: typeFilter === '全部' ? undefined : typeFilter,
      province: provinceFilter === '全部' ? undefined : provinceFilter,
    })
      .then((res) => {
        setSchools(res.data);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      })
      .catch(() => {
        setSchools([]);
        setTotal(0);
        setTotalPages(1);
      })
      .finally(() => setLoading(false));
  }, [currentPage, search, levelFilter, typeFilter, provinceFilter]);

  // Reset to page 1 when filters change
  const handleFilterChange = (setter: (v: string) => void) => (v: string) => {
    setter(v);
    setCurrentPage(1);
  };

  // Hero stats counters
  const [heroRef, setHeroRef] = useState<HTMLDivElement | null>(null);
  const [heroInView, setHeroInView] = useState(false);
  useEffect(() => {
    if (!heroRef) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setHeroInView(true); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    observer.observe(heroRef);
    return () => observer.disconnect();
  }, [heroRef]);

  const schoolsCount = useCountUp(metaTotal, 2, heroInView);
  const provincesCount = useCountUp(metaProvinceCount, 2, heroInView);

  const staggerContainer = {
    hidden: {},
    visible: {
      transition: { staggerChildren: 0.03 },
    },
  };

  const staggerItem = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Hero Area */}
        <motion.div
          ref={setHeroRef}
          className="gradient-hero rounded-2xl p-8 md:p-12 mb-10 overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="relative z-10">
            <h1 className="font-serif text-h2 text-white mb-3">院校排名</h1>
            <p className="font-sans text-lg font-light italic text-white/70 mb-8">
              基于历年录取数据，发现最适合你的大学
            </p>
            <div className="flex flex-wrap gap-8">
              <div>
                <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-white/40 mb-1">收录院校</div>
                <div className="font-serif text-2xl text-white">{heroInView ? schoolsCount : 0}</div>
              </div>
              <div>
                <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-white/40 mb-1">覆盖省份</div>
                <div className="font-serif text-2xl text-white">{heroInView ? provincesCount : 0}</div>
              </div>
              <div>
                <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-white/40 mb-1">数据年份</div>
                <div className="font-serif text-2xl text-white">2023-2025</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Two-column layout: sidebar + main */}
        <div className="flex flex-col lg:flex-row gap-8">

          {/* Left Sidebar - hidden on mobile */}
          <div className="hidden lg:flex flex-col gap-6 w-80 shrink-0">
            <div className="sticky top-32 space-y-6">
              <StatsSidebar
                totalSchools={metaTotal}
                levelCounts={[
                  { level: '985', count: metaLevelCounts['985'] || 0 },
                  { level: '211', count: metaLevelCounts['211'] || 0 },
                  { level: '双一流', count: metaLevelCounts['双一流'] || 0 },
                  { level: '普通', count: metaLevelCounts['普通'] || 0 },
                ]}
                provinceCounts={Object.entries(metaProvinceCounts)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 10)
                  .map(([province, count]) => ({ province, count }))}
              />
              <QuickTips />
              <RelatedLinks />
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">

        {/* Search & Filters */}
        <motion.div
          className="card-premium p-6 mb-6 bg-white/80 backdrop-blur-sm"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6 }}
        >
          {/* Search */}
          <div className="relative mb-5">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-beige-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="搜索院校名称、省份、标签..."
              className="w-full pl-10 pr-4 py-3 bg-beige-50 border border-[#E0D8CC] rounded-lg font-sans text-sm font-light text-brand-900 placeholder:text-beige-500 focus:outline-none focus:ring-2 focus:ring-[#C4A45C]/30 focus:border-[#C4A45C]/50 transition-all"
            />
          </div>

          {/* Level Filters */}
          <div className="mb-4">
            <div className="font-mono text-caption-mono text-beige-500 mb-2">院校层次</div>
            <div className="flex flex-wrap gap-2">
              {LEVEL_FILTERS.map((level) => (
                <motion.button
                  key={level}
                  onClick={() => handleFilterChange(setLevelFilter)(level)}
                  className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-[0.15em] transition-all ${
                    levelFilter === level
                      ? 'bg-[#1A2E22] text-white shadow-sm'
                      : 'bg-[#F0EAE0] text-beige-600 hover:bg-beige-200'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {level}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Type Filters */}
          <div className="mb-4">
            <div className="font-mono text-caption-mono text-beige-500 mb-2">院校类型</div>
            <div className="flex flex-wrap gap-2">
              {TYPE_FILTERS.map((type) => (
                <motion.button
                  key={type}
                  onClick={() => handleFilterChange(setTypeFilter)(type)}
                  className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-[0.15em] transition-all ${
                    typeFilter === type
                      ? 'bg-[#1A2E22] text-white shadow-sm'
                      : 'bg-[#F0EAE0] text-beige-600 hover:bg-beige-200'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {type}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Province Filters */}
          <div>
            <div className="font-mono text-caption-mono text-beige-500 mb-2">所在地</div>
            <div className="flex flex-wrap gap-2">
              {provinces.map((province) => (
                <motion.button
                  key={province}
                  onClick={() => handleFilterChange(setProvinceFilter)(province)}
                  className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-[0.15em] transition-all ${
                    provinceFilter === province
                      ? 'bg-[#1A2E22] text-white shadow-sm'
                      : 'bg-[#F0EAE0] text-beige-600 hover:bg-beige-200'
                  }`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {province}
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Results count */}
        <motion.div
          className="font-mono text-caption-mono text-beige-500 mb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          共 {total} 所院校
        </motion.div>

        {/* Ranking Table */}
        <motion.div
          className="card-premium overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.6 }}
        >
          {/* Table Header */}
          <div className="hidden md:grid grid-cols-[60px_1fr_100px_100px_120px_1fr] gap-4 px-6 py-4 bg-[#F5F0E8] border-b border-[#E0D8CC]">
            <div className="font-mono text-caption-mono text-beige-500 text-center">#</div>
            <div className="font-mono text-caption-mono text-beige-500">院校</div>
            <div className="font-mono text-caption-mono text-beige-500">层次</div>
            <div className="font-mono text-caption-mono text-beige-500">类型</div>
            <div className="font-mono text-caption-mono text-beige-500">所在地</div>
            <div className="font-mono text-caption-mono text-beige-500">标签</div>
          </div>

          {/* Table Rows */}
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            <AnimatePresence mode="wait">
              {schools.map((school, i) => (
                <motion.div
                  key={school.id}
                  className="grid grid-cols-1 md:grid-cols-[60px_1fr_100px_100px_120px_1fr] gap-4 px-6 py-5 items-center border-b border-[#E0D8CC] last:border-b-0 hover:bg-[#F5F0E8]/30 transition-all"
                  variants={staggerItem}
                  exit={{ opacity: 0, y: -10 }}
                  whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(26,46,34,0.06)' }}
                >
                  {/* Rank */}
                  <div className="text-center">
                    {school.ranking <= 3 ? (
                      <motion.span
                        className="text-lg inline-block"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 10 }}
                      >
                        {['','🥇','🥈','🥉'][school.ranking]}
                      </motion.span>
                    ) : (
                      <span className="font-mono text-sm text-beige-500">
                        {String(school.ranking).padStart(2, '0')}
                      </span>
                    )}
                  </div>

                  {/* School Name + Badge */}
                  <div className="flex items-center gap-3 min-w-0">
                    <SchoolBadge slug={school.slug} name={school.name} size={40} />
                    <Link
                      to={`/university/${school.slug}`}
                      className="font-serif text-base font-normal text-brand-900 hover:text-brand-700 transition-colors truncate"
                    >
                      {school.name}
                    </Link>
                  </div>

                  {/* Level */}
                  <div>
                    <Badge variant={getLevelBadgeVariant(school.level)} size="sm">
                      {school.level}
                    </Badge>
                  </div>

                  {/* Type */}
                  <div className="font-sans text-sm font-light text-beige-600">
                    {school.type}
                  </div>

                  {/* Location */}
                  <div className="flex items-center gap-1.5 font-sans text-sm font-light text-beige-600">
                    <MapPin size={12} className="shrink-0" />
                    <span className="truncate">{school.city}</span>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5">
                    {school.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="font-mono text-[9px] uppercase tracking-[0.1em] text-beige-500 bg-[#F0EAE0] px-2 py-0.5 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                    {school.tags.length > 2 && (
                      <span className="font-mono text-[9px] text-beige-400">
                        +{school.tags.length - 2}
                      </span>
                    )}
                  </div>

                  {/* Mobile-only extra info */}
                  <div className="md:hidden col-span-full flex flex-wrap items-center gap-3 mt-1">
                    <Badge variant={getLevelBadgeVariant(school.level)} size="sm">
                      {school.level}
                    </Badge>
                    <span className="font-sans text-xs font-light text-beige-600">{school.type}</span>
                    <span className="flex items-center gap-1 font-sans text-xs font-light text-beige-600">
                      <MapPin size={10} />
                      {school.city}
                    </span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>

          {/* Empty state */}
          {schools.length === 0 && !loading && (
            <motion.div
              className="text-center py-20"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="w-16 h-16 rounded-full bg-beige-200 flex items-center justify-center mx-auto mb-4">
                <Search size={24} className="text-beige-500" />
              </div>
              <p className="font-sans text-base font-light text-beige-600">没有找到匹配的院校</p>
              <p className="font-sans text-xs font-light text-beige-500 mt-1">试试调整筛选条件</p>
            </motion.div>
          )}
        </motion.div>

        {/* Pagination */}
        {totalPages > 1 && (
          <motion.div
            className="flex items-center justify-center gap-2 mt-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <motion.button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="flex items-center gap-1 px-3 py-2 rounded-lg font-mono text-[10px] uppercase tracking-[0.15em] text-beige-600 bg-white border border-[#E0D8CC] hover:bg-beige-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <ChevronLeft size={14} />
              上一页
            </motion.button>
            {(() => {
              const range = (start: number, end: number) =>
                Array.from({ length: end - start + 1 }, (_, i) => start + i);
              const pages: (number | string)[] = [];
              const maxVisible = 9;

              if (totalPages <= maxVisible) {
                pages.push(...range(1, totalPages));
              } else {
                pages.push(1);
                const half = 3;
                let start = Math.max(2, currentPage - half);
                let end = Math.min(totalPages - 1, currentPage + half);
                if (end - start + 1 < 7) {
                  if (start === 2) end = Math.min(totalPages - 1, start + 6);
                  else start = Math.max(2, end - 6);
                }
                if (start > 2) pages.push('...');
                pages.push(...range(start, end));
                if (end < totalPages - 1) pages.push('...');
                pages.push(totalPages);
              }

              return pages.map((page, idx) =>
                page === '...' ? (
                  <span key={`dots-${idx}`} className="w-9 h-9 flex items-center justify-center font-mono text-xs text-beige-400">
                    ...
                  </span>
                ) : (
                  <motion.button
                    key={page}
                    onClick={() => setCurrentPage(page as number)}
                    className={`w-9 h-9 rounded-lg font-mono text-xs transition-all ${
                      currentPage === page
                        ? 'bg-[#1A2E22] text-white shadow-sm'
                        : 'text-beige-600 bg-white border border-[#E0D8CC] hover:bg-beige-50'
                    }`}
                    whileHover={{ scale: currentPage === page ? 1 : 1.08 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {page}
                  </motion.button>
                )
              );
            })()}
            <motion.button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="flex items-center gap-1 px-3 py-2 rounded-lg font-mono text-[10px] uppercase tracking-[0.15em] text-beige-600 bg-white border border-[#E0D8CC] hover:bg-beige-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              下一页
              <ChevronRight size={14} />
            </motion.button>
          </motion.div>
        )}

          </div>{/* end main content */}
        </div>{/* end two-column */}
      </div>
    </div>
  );
}
