import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin,
  Globe,
  ArrowLeft,
  ExternalLink,
  RefreshCw,
  Phone,
  ChevronDown,
  ChevronUp,
  Building2,
  BookOpen,
  GraduationCap,
  FileText,
} from 'lucide-react';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { fetchChsiSchoolDetail, type ChsiSchoolDetail } from '../services/chsiSchool';
import { fetchSchoolBySlug } from '../services/school';
import SchoolBadge from '../components/school/SchoolBadge';

/* ------------------------------------------------------------------ */
/*  Types & Constants                                                  */
/* ------------------------------------------------------------------ */

type TabId = 'overview' | 'majors' | 'departments' | 'policies' | 'campuses';

interface TabDef {
  id: TabId;
  label: string;
  icon: React.ComponentType<any>;
}

const TABS: TabDef[] = [
  { id: 'overview', label: '院校概况', icon: Building2 },
  { id: 'majors', label: '专业设置', icon: BookOpen },
  { id: 'departments', label: '院系设置', icon: GraduationCap },
  { id: 'policies', label: '招生章程', icon: FileText },
  { id: 'campuses', label: '校园信息', icon: MapPin },
];

/* ------------------------------------------------------------------ */
/*  Animation variants                                                 */
/* ------------------------------------------------------------------ */

const tabVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, delay: i * 0.05, ease: 'easeOut' },
  }),
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function getTagColor(tag: string): string {
  const known: Record<string, string> = {
    985: 'bg-blue-100 text-blue-800',
    211: 'bg-indigo-100 text-indigo-800',
    双一流: 'bg-emerald-100 text-emerald-800',
    C9: 'bg-purple-100 text-purple-800',
    研究生院: 'bg-amber-100 text-amber-800',
  };
  return known[tag] || 'bg-[#1A2E22]/10 text-[#1A2E22]';
}

function formatDate(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function UniversityDetail() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [schoolData, setSchoolData] = useState<ChsiSchoolDetail | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [expandedMajorCategory, setExpandedMajorCategory] = useState<number | null>(null);

  /* ---- data loading ------------------------------------------------ */

  const loadData = useCallback(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const fetchData = slug.includes('%') || slug.includes('大学') || slug.includes('学院')
      ? Promise.resolve(slug)
      : fetchSchoolBySlug(slug)
          .then((s: any) => s?.data?.name || s?.name || slug)
          .catch(() => slug);

    fetchData
      .then((name: string) => fetchChsiSchoolDetail(name))
      .then((data) => {
        if (data.error) {
          setError(data.error);
          setSchoolData(null);
        } else {
          setSchoolData(data);
        }
      })
      .catch((err: Error) => {
        setError(err.message || '加载失败，请稍后重试');
      })
      .finally(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /* ---- derived data ------------------------------------------------ */

  const tags = schoolData?.tags ?? [];
  const basicInfo = schoolData?.basic_info;
  const infoRows = basicInfo
    ? [
        { label: '主管部门', value: basicInfo.department },
        { label: '所在城市', value: basicInfo.province && basicInfo.city ? `${basicInfo.province} ${basicInfo.city}` : basicInfo.province || basicInfo.city },
        { label: '办学层次', value: basicInfo.level },
        { label: '院校类型', value: basicInfo.type },
        { label: '办学性质', value: basicInfo.is_public ? '公办' : '民办' },
        { label: '招生电话', value: schoolData?.contact_phone || schoolData?.basic_info?.province },
      ].filter((r) => r.value)
    : [];

  /* ---- render helpers ---------------------------------------------- */

  const renderTags = () =>
    tags.length > 0 && (
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <span
            key={tag}
            className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${getTagColor(tag)}`}
          >
            {tag}
          </span>
        ))}
      </div>
    );

  /* ---- loading state ------------------------------------------------ */

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F5F0E8] flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  /* ---- error state -------------------------------------------------- */

  if (error || !schoolData) {
    return (
      <div className="min-h-screen bg-[#F5F0E8] flex items-center justify-center">
        <div className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-8 max-w-md w-full text-center">
          <p className="text-[#4A4A4A] mb-4">{error || '未找到院校信息'}</p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 rounded-lg border border-[#E0D8CC] text-[#4A4A4A] text-sm hover:bg-[#1A2E22]/5 transition-colors"
            >
              返回
            </button>
            <button
              onClick={loadData}
              className="px-4 py-2 rounded-lg bg-[#1A2E22] text-[#F5F0E8] text-sm hover:bg-[#1A2E22]/90 transition-colors inline-flex items-center gap-1.5"
            >
              <RefreshCw size={14} />
              重试
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ---- main render -------------------------------------------------- */

  return (
    <div className="bg-[#F5F0E8]">
      {/* ---- Header ---------------------------------------------------- */}
      <div className="max-w-4xl mx-auto px-4 pt-6 pb-4">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-sm text-[#6B5E4E] hover:text-[#1A2E22] transition-colors mb-4"
        >
          <ArrowLeft size={16} />
          返回院校列表
        </button>

        <div className="flex items-start gap-5">
          {/* Badge */}
          <div className="shrink-0">
            <SchoolBadge slug={slug || ''} name={schoolData.school_name} size={72} />
          </div>

          {/* Info */}
          <div className="min-w-0 flex-1">
            <h1 className="font-serif text-3xl md:text-4xl font-medium text-[#1A2E22] leading-tight">
              {schoolData.school_name}
            </h1>

            {/* Tags */}
            <div className="mt-2">{renderTags()}</div>

            {/* Source + cache indicator */}
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="font-sans text-xs text-[#8B7E6E]">
                数据来源：教育部阳光高考平台
              </span>
              {schoolData.from_cache ? (
                <span className="inline-flex items-center gap-1 text-xs text-[#8B7E6E] bg-[#1A2E22]/5 px-2 py-0.5 rounded-full">
                  <RefreshCw size={10} />
                  缓存数据
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  最新数据
                </span>
              )}
              {schoolData.generated_at && (
                <span className="text-xs text-[#8B7E6E]">
                  {formatDate(schoolData.generated_at)}
                </span>
              )}
            </div>

            {/* Links + phone */}
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
              {schoolData.official_site && (
                <a
                  href={schoolData.official_site}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-[#A8883C] hover:text-[#8B7330] transition-colors"
                >
                  <Globe size={14} />
                  官方网站
                  <ExternalLink size={12} />
                </a>
              )}
              {schoolData.admission_site && (
                <a
                  href={schoolData.admission_site}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-[#A8883C] hover:text-[#8B7330] transition-colors"
                >
                  <MapPin size={14} />
                  招生官网
                  <ExternalLink size={12} />
                </a>
              )}
              {schoolData.contact_phone && (
                <span className="inline-flex items-center gap-1 text-sm text-[#6B5E4E]">
                  <Phone size={14} />
                  {schoolData.contact_phone}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ---- Tab Bar (sticky) ----------------------------------------- */}
      <div className="sticky top-0 z-20 bg-[#F5F0E8] border-b border-[#E0D8CC]">
        <div className="max-w-4xl mx-auto px-4">
          <nav className="flex gap-1 -mb-px overflow-x-auto scrollbar-none">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`shrink-0 flex items-center gap-1.5 px-3.5 py-3 text-sm font-medium border-b-2 transition-all ${
                    isActive
                      ? 'border-[#1A2E22] text-[#1A2E22]'
                      : 'border-transparent text-[#4A4A4A] hover:text-[#1A2E22] hover:bg-[#1A2E22]/5'
                  }`}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* ---- Tab Content ---------------------------------------------- */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-6"
            >
              {/* Overview text */}
              {schoolData.overview && (
                <motion.div
                  className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5 md:p-6"
                  custom={0}
                  variants={cardVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <h2 className="font-serif text-xl font-medium text-[#1A2E22] mb-3">学校简介</h2>
                  <p className="font-sans text-base font-light text-[#4A4A4A] leading-relaxed whitespace-pre-line">
                    {schoolData.overview}
                  </p>
                </motion.div>
              )}

              {/* Basic info grid */}
              {infoRows.length > 0 && (
                <motion.div
                  className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5 md:p-6"
                  custom={1}
                  variants={cardVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <h2 className="font-serif text-xl font-medium text-[#1A2E22] mb-4">基本信息</h2>
                  <div className="divide-y divide-[#E0D8CC]">
                    {infoRows.map((row) => (
                      <div
                        key={row.label}
                        className="flex items-baseline gap-2 py-2.5 first:pt-0 last:pb-0"
                      >
                        <span className="font-sans text-sm text-[#6B5E4E] shrink-0 w-20">
                          {row.label}
                        </span>
                        <span className="font-sans text-sm text-[#1A2E22]">{row.value}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Tags section */}
              {tags.length > 0 && (
                <motion.div
                  className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5 md:p-6"
                  custom={2}
                  variants={cardVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <h2 className="font-serif text-xl font-medium text-[#1A2E22] mb-3">院校标签</h2>
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <span
                        key={tag}
                        className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getTagColor(tag)}`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Source attribution */}
              <motion.p
                className="text-xs text-[#8B7E6E] text-center"
                custom={3}
                variants={cardVariants}
                initial="hidden"
                animate="visible"
              >
                数据来源：教育部阳光高考平台
              </motion.p>
            </motion.div>
          )}

          {activeTab === 'majors' && (
            <motion.div
              key="majors"
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-2"
            >
              {(schoolData.major_categories ?? []).length === 0 ? (
                <div className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-8 text-center">
                  <p className="text-[#8B7E6E] text-sm">暂无专业信息</p>
                </div>
              ) : (
                (schoolData.major_categories ?? []).map((cat, idx) => {
                  const isOpen = expandedMajorCategory === idx;
                  return (
                    <motion.div
                      key={cat.name}
                      className="bg-white border border-[#E0D8CC] rounded-xl overflow-hidden"
                      custom={idx}
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                    >
                      <button
                        onClick={() =>
                          setExpandedMajorCategory(isOpen ? null : idx)
                        }
                        className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-[#1A2E22]/5 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-sans text-sm font-medium text-[#1A2E22]">
                            {cat.name}
                          </span>
                          <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-[#1A2E22]/10 text-[#1A2E22] text-xs font-medium">
                            {cat.majors.length}
                          </span>
                        </div>
                        {isOpen ? (
                          <ChevronUp size={16} className="text-[#6B5E4E] shrink-0" />
                        ) : (
                          <ChevronDown size={16} className="text-[#6B5E4E] shrink-0" />
                        )}
                      </button>
                      <AnimatePresence>
                        {isOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2, ease: 'easeInOut' }}
                            className="overflow-hidden"
                          >
                            <div className="px-5 pb-4 pt-1 flex flex-wrap gap-2 border-t border-[#E0D8CC]">
                              {cat.majors.map((major) => (
                                <span
                                  key={major}
                                  className="inline-flex px-3 py-1 rounded-full bg-[#1A2E22]/5 text-[#1A2E22] text-xs font-medium"
                                >
                                  {major}
                                </span>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}

          {activeTab === 'departments' && (
            <motion.div
              key="departments"
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-6"
            >
              {(schoolData.departments ?? []).length === 0 ? (
                <div className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-8 text-center">
                  <p className="text-[#8B7E6E] text-sm">暂无院系信息</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(schoolData.departments ?? []).map((dept, idx) => (
                    <motion.div
                      key={dept.name}
                      className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5"
                      custom={idx}
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                    >
                      <h3 className="font-serif text-base font-medium text-[#1A2E22] mb-1.5">
                        {dept.name}
                      </h3>
                      {dept.description && (
                        <p className="font-sans text-sm font-light text-[#4A4A4A] leading-relaxed">
                          {dept.description}
                        </p>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'policies' && (
            <motion.div
              key="policies"
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-4"
            >
              {/* Summary */}
              {schoolData.admission_summary && (
                <motion.div
                  className="bg-[#A8883C]/10 border border-[#A8883C]/20 rounded-2xl p-5 md:p-6"
                  custom={0}
                  variants={cardVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <p className="font-sans text-sm font-light text-[#4A4A4A] leading-relaxed">
                    {schoolData.admission_summary}
                  </p>
                </motion.div>
              )}

              {/* Policy clauses */}
              {(schoolData.admission_policies ?? []).length === 0 ? (
                <div className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-8 text-center">
                  <p className="text-[#8B7E6E] text-sm">暂无招生章程信息</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {(schoolData.admission_policies ?? []).map((policy, idx) => (
                    <motion.div
                      key={policy.clause_number || idx}
                      className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5 md:p-6 flex gap-4"
                      custom={idx + 1}
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                    >
                      <span className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-[#1A2E22] text-[#F5F0E8] text-sm font-medium">
                        {policy.clause_number?.replace(/[^\d]/g, '') || idx + 1}
                      </span>
                      <div className="min-w-0">
                        {policy.title && (
                          <h3 className="font-sans text-sm font-medium text-[#1A2E22] mb-1">
                            {policy.title}
                          </h3>
                        )}
                        <p className="font-sans text-sm font-light text-[#4A4A4A] leading-relaxed whitespace-pre-line">
                          {policy.content}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'campuses' && (
            <motion.div
              key="campuses"
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-6"
            >
              {(schoolData.campuses ?? []).length === 0 ? (
                <div className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-8 text-center">
                  <p className="text-[#8B7E6E] text-sm">暂无校园信息</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(schoolData.campuses ?? []).map((campus, idx) => (
                    <motion.div
                      key={campus.name}
                      className="bg-white border border-[#E0D8CC] rounded-2xl shadow-sm p-5"
                      custom={idx}
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                    >
                      <h3 className="font-serif text-base font-medium text-[#1A2E22] mb-2">
                        {campus.name}
                      </h3>
                      <div className="space-y-1.5">
                        <div className="flex items-start gap-2">
                          <MapPin
                            size={14}
                            className="shrink-0 mt-0.5 text-[#6B5E4E]"
                          />
                          <span className="font-sans text-sm font-light text-[#4A4A4A]">
                            {campus.address || '暂无地址信息'}
                          </span>
                        </div>
                        {campus.phone && (
                          <div className="flex items-center gap-2">
                            <Phone
                              size={14}
                              className="shrink-0 text-[#6B5E4E]"
                            />
                            <span className="font-sans text-sm font-light text-[#4A4A4A]">
                              {campus.phone}
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
