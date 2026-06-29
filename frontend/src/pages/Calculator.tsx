import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Crosshair, Map, Building2, GraduationCap, Check } from 'lucide-react';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import StepIndicator from '../components/common/StepIndicator';
import { isValidScore, isValidRank } from '../utils/validators';
import QuickTips from '../components/panels/QuickTips';
import RelatedLinks from '../components/panels/RelatedLinks';

type ExamType = '综合' | '物理' | '历史' | '物理类' | '历史类';
type Priority = 'school' | 'major' | 'city';

interface ProvinceConfig {
  score_max: number;
  exam_mode: string;
  subject_options: string[];
  subject_type_default: string;
  hint_subject: string;
  hint_score: string;
}

const PROVINCES = ['江苏'];

const INTERESTS = [
  '计算机/IT', '医学/药学', '金融/经济', '法学/政治', '教育/师范',
  '工程/制造', '理学/基础科学', '传媒/艺术', '农林/环境', '语言/文学',
  '管理/商科', '体育/运动',
];

const INTEREST_SUB_OPTIONS: Record<string, string[]> = {
  '计算机/IT': ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '网络安全', '物联网工程', '数字媒体技术'],
  '医学/药学': ['临床医学', '口腔医学', '药学', '中医学', '护理学', '医学影像学', '预防医学'],
  '金融/经济': ['金融学', '经济学', '会计学', '国际经济与贸易', '财政学', '保险学', '投资学'],
  '法学/政治': ['法学', '知识产权', '政治学', '社会学', '国际政治', '行政管理'],
  '教育/师范': ['教育学', '汉语言文学(师范)', '数学(师范)', '英语(师范)', '小学教育', '学前教育'],
  '工程/制造': ['机械工程', '电气工程', '自动化', '土木工程', '建筑学', '材料科学', '车辆工程'],
  '理学/基础科学': ['数学与应用数学', '物理学', '化学', '生物科学', '统计学', '心理学', '地理科学', '大气科学', '海洋科学', '地质学'],
  '传媒/艺术': ['新闻学', '广告学', '广播电视学', '设计学', '美术学', '音乐学', '戏剧影视'],
  '农林/环境': ['农学', '林学', '环境工程', '食品科学', '生态学'],
  '语言/文学': ['汉语言文学', '英语', '日语', '法语', '翻译', '历史学', '哲学'],
  '管理/商科': ['工商管理', '市场营销', '人力资源管理', '物流管理', '电子商务', '旅游管理'],
  '体育/运动': ['体育教育', '运动训练', '社会体育指导', '武术与民族传统体育', '运动康复', '休闲体育'],
};

const REGION_CITY_MAP: Record<string, string[]> = {
  '长三角': ['南京', '苏州', '无锡', '杭州', '上海', '宁波', '常州', '镇江', '扬州', '南通'],
  '京津冀': ['北京', '天津', '石家庄', '保定', '唐山'],
  '珠三角': ['广州', '深圳', '珠海', '佛山', '东莞', '中山'],
  '华中地区': ['武汉', '长沙', '郑州', '南昌', '合肥'],
  '西南地区': ['成都', '重庆', '昆明', '贵阳'],
  '西北地区': ['西安', '兰州', '乌鲁木齐'],
  '东北地区': ['哈尔滨', '长春', '沈阳', '大连'],
};

const TIERS = ['985高校', '211高校', '双一流', '省重点', '公办本科'];

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 300 : -300,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? -300 : 300,
    opacity: 0,
  }),
};

export default function Calculator() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState(1);
  const [formData, setFormData] = useState({
    province: '',
    examType: '物理' as ExamType,
    score: '',
    rank: '',
    interests: [] as string[],
    regions: [] as string[],
    priority: 'school' as Priority,
    selectedSubjects: [] as string[],
    selectedInterests: [] as string[],
    selectedCities: [] as string[],
    tiers: [] as string[],
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [provinceConfig, setProvinceConfig] = useState<ProvinceConfig | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  /** Compute parent interest categories from selected sub-options */
  const computeInterestsFromSelected = (selected: string[]): string[] => {
    const result: string[] = [];
    for (const [category, subs] of Object.entries(INTEREST_SUB_OPTIONS)) {
      if (subs.some((s) => selected.includes(s))) {
        result.push(category);
      }
    }
    return result;
  };

  /** Compute parent regions from selected cities */
  const computeRegionsFromCities = (cities: string[]): string[] => {
    const result: string[] = [];
    for (const [region, cityList] of Object.entries(REGION_CITY_MAP)) {
      if (cityList.some((c) => cities.includes(c))) {
        result.push(region);
      }
    }
    return result;
  };

  const fetchProvinceConfig = async (code: string) => {
    try {
      const res = await fetch(`/api/v1/province-config/${code}`);
      const data = await res.json();
      return data;
    } catch {
      return null;
    }
  };

  const handleProvinceChange = async (code: string) => {
    setFormData((prev) => ({ ...prev, province: code }));
    if (!code) {
      setProvinceConfig(null);
      return;
    }
    const config = await fetchProvinceConfig(code);
    if (config) {
      setProvinceConfig(config);
      const defaultType = config.subject_type_default;
      // Map API values to internal: 物理类→物理, 历史类→历史
      const mapped = defaultType === '物理类' ? '物理' : defaultType === '历史类' ? '历史' : defaultType;
      if (['综合', '物理', '历史'].includes(mapped)) {
        setFormData((prev) => ({ ...prev, examType: mapped as ExamType }));
      }
    }
  };

  const validateStep = (s: number): boolean => {
    const newErrors: Record<string, string> = {};
    const maxScore = provinceConfig?.score_max ?? 750;

    if (s === 1) {
      if (!formData.province) newErrors.province = '请选择省份';
      if (!formData.score || !isValidScore(Number(formData.score), maxScore)) {
        newErrors.score = `请输入有效分数（0-${maxScore}）`;
      }
      if (!formData.rank || !isValidRank(Number(formData.rank))) {
        newErrors.rank = '请输入有效位次';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setDirection(1);
      setStep((prev) => Math.min(prev + 1, 3));
    }
  };

  const handlePrev = () => {
    setDirection(-1);
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = () => {
    // Jiangsu uses dedicated recommendation engine
    if (formData.province === '江苏') {
      navigate('/jiangsu-results', {
        state: {
          score: Number(formData.score),
          rank: Number(formData.rank),
          examType: formData.examType,
          interests: formData.interests,
          regions: formData.regions,
          selectedInterests: formData.selectedInterests,
          selectedCities: formData.selectedCities,
          tiers: formData.tiers,
          priority: formData.priority,
          selectedSubjects: formData.selectedSubjects,
        },
      });
      return;
    }
    navigate('/preview', {
      state: {
        score: Number(formData.score),
        rank: Number(formData.rank),
        province: formData.province,
        examType: formData.examType,
        interests: formData.interests,
        regions: formData.regions,
        selectedInterests: formData.selectedInterests,
        selectedCities: formData.selectedCities,
        tiers: formData.tiers,
        priority: formData.priority,
      },
    });
  };

  const toggleInterestCategory = (category: string) => {
    const subs = INTEREST_SUB_OPTIONS[category] || [];
    setFormData((prev) => {
      const allSelected = subs.every((s) => prev.selectedInterests.includes(s));
      const next = allSelected
        ? prev.selectedInterests.filter((s) => !subs.includes(s))
        : [...new Set([...prev.selectedInterests, ...subs])];
      return {
        ...prev,
        selectedInterests: next,
        interests: computeInterestsFromSelected(next),
      };
    });
  };

  const toggleSubInterest = (sub: string) => {
    setFormData((prev) => {
      const next = prev.selectedInterests.includes(sub)
        ? prev.selectedInterests.filter((s) => s !== sub)
        : [...prev.selectedInterests, sub];
      return {
        ...prev,
        selectedInterests: next,
        interests: computeInterestsFromSelected(next),
      };
    });
  };

  const toggleCity = (city: string) => {
    setFormData((prev) => {
      const next = prev.selectedCities.includes(city)
        ? prev.selectedCities.filter((c) => c !== city)
        : [...prev.selectedCities, city];
      return {
        ...prev,
        selectedCities: next,
        regions: computeRegionsFromCities(next),
      };
    });
  };

  const selectAllCitiesInRegion = (region: string) => {
    const cities = REGION_CITY_MAP[region];
    if (!cities) return;
    setFormData((prev) => {
      const allAlreadySelected = cities.every((c) => prev.selectedCities.includes(c));
      const next = allAlreadySelected
        ? prev.selectedCities.filter((c) => !cities.includes(c))
        : [...new Set([...prev.selectedCities, ...cities])];
      return {
        ...prev,
        selectedCities: next,
        regions: computeRegionsFromCities(next),
      };
    });
  };

  const toggleTier = (tier: string) => {
    setFormData((prev) => ({
      ...prev,
      tiers: prev.tiers.includes(tier)
        ? prev.tiers.filter((t) => t !== tier)
        : [...prev.tiers, tier],
    }));
  };

  const subjectOptions = provinceConfig?.subject_options || ['综合', '物理', '历史'];
  const scoreHint = provinceConfig?.hint_score || '满分 750';

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="font-serif text-h2 text-brand-900 mb-3">志愿评估</h1>
          <p className="font-sans text-lg font-light italic text-beige-600">
            填写信息，获取你的专属志愿方案
          </p>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-8">

          {/* Left: Form */}
          <div className="flex-1 min-w-0">

        {/* Step Indicator */}
        <motion.div
          className="mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6 }}
        >
          <StepIndicator
            currentStep={step}
            totalSteps={3}
            labels={['基本信息', '兴趣偏好', '确认提交']}
          />
        </motion.div>

        {/* Steps with slide animation */}
        <AnimatePresence mode="wait" custom={direction}>
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <motion.div
              key="step1"
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="space-y-6"
            >
              <div className="card-premium p-8 md:p-10 space-y-6">
                <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-6">
                  基本信息
                </h3>

                {/* Province */}
                <div className="flex flex-col gap-1.5">
                  <label className="font-sans text-sm font-normal text-brand-900/80 tracking-wide">
                    所在省份
                  </label>
                  <select
                    value={formData.province}
                    onChange={(e) => handleProvinceChange(e.target.value)}
                    className="w-full px-4 py-3 bg-white border border-[#E0D8CC] rounded-lg font-sans font-light text-brand-900 focus:outline-none focus:ring-2 focus:ring-[#C4A45C]/30 focus:border-[#C4A45C]/50 appearance-none transition-all"
                  >
                    <option value="">请选择省份</option>
                    {PROVINCES.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                  {errors.province && (
                    <span className="font-sans text-xs text-[#A84A3A]">{errors.province}</span>
                  )}
                </div>

                {/* Exam Type */}
                <div className="flex flex-col gap-1.5">
                  <label className="font-sans text-sm font-normal text-brand-900/80 tracking-wide">
                    考试类型
                    {provinceConfig?.exam_mode && (
                      <span className="ml-2 font-mono text-caption-mono text-beige-500">
                        ({provinceConfig.exam_mode})
                      </span>
                    )}
                  </label>
                  <div className="flex gap-3">
                    {subjectOptions.map((type) => (
                      <button
                        key={type}
                        onClick={() => setFormData((prev) => ({ ...prev, examType: type as ExamType }))}
                        className={`flex-1 py-3 px-4 rounded-lg font-mono text-caption-mono transition-all duration-200 ${
                          formData.examType === type
                            ? 'bg-brand-700 text-white shadow-sm'
                            : 'bg-beige-100 text-beige-600 hover:bg-beige-200'
                        }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Subject Selection (REAL, not hardcoded) */}
                <div className="flex flex-col gap-1.5">
                  <label className="font-sans text-sm font-normal text-brand-900/80 tracking-wide">
                    再选科目
                    <span className="ml-1 font-mono text-caption-mono text-beige-500">（选填，不选则标记为需核验）</span>
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {['化学', '生物', '政治', '地理'].map(subj => {
                      const isSelected = formData.selectedSubjects.includes(subj);
                      return (
                        <button key={subj} type="button"
                          onClick={() => setFormData(prev => ({
                            ...prev,
                            selectedSubjects: isSelected
                              ? prev.selectedSubjects.filter(s => s !== subj)
                              : [...prev.selectedSubjects, subj]
                          }))}
                          className={`px-4 py-2 rounded-lg font-sans text-sm font-light transition-all ${
                            isSelected
                              ? 'bg-brand-700 text-white shadow-sm'
                              : 'bg-beige-100 text-beige-700 hover:bg-beige-200'
                          }`}
                        >{subj}</button>
                      );
                    })}
                  </div>
                </div>

                {/* Score & Rank */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="高考分数"
                    type="number"
                    placeholder={scoreHint}
                    value={formData.score}
                    onChange={(e) => setFormData((prev) => ({ ...prev, score: e.target.value }))}
                    error={errors.score}
                    hint={scoreHint}
                  />
                  <Input
                    label="全省位次"
                    type="number"
                    placeholder="如：26843"
                    value={formData.rank}
                    onChange={(e) => setFormData((prev) => ({ ...prev, rank: e.target.value }))}
                    error={errors.rank}
                    hint="一分一段表中的位次"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button variant="gold" size="lg" onClick={handleNext}>
                  下一步
                </Button>
              </div>
            </motion.div>
          )}

                    {/* Step 2: Preferences */}
          {step === 2 && (
            <motion.div
              key="step2"
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="space-y-6"
            >
              <div className="card-premium p-8 md:p-10 space-y-8">

                {/* Section 1: 兴趣方向 */}
                <div>
                  <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-2">
                    兴趣方向
                  </h3>
                  <p className="font-sans text-sm font-light text-beige-600 mb-4">
                    选择感兴趣的专业方向（点击大类切换全部子项）
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {INTERESTS.map((category) => {
                      const subs = INTEREST_SUB_OPTIONS[category] || [];
                      const selectedCount = subs.filter((s) => formData.selectedInterests.includes(s)).length;
                      const allSelected = subs.length > 0 && selectedCount === subs.length;
                      const partial = selectedCount > 0 && selectedCount < subs.length;
                      return (
                        <button
                          key={category}
                          type="button"
                          onClick={() => toggleInterestCategory(category)}
                          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-sans text-sm font-light transition-all duration-200 ${
                            allSelected
                              ? 'bg-brand-700 text-white shadow-sm'
                              : partial
                                ? 'bg-brand-700/60 text-white'
                                : 'bg-beige-100 text-beige-700 hover:bg-beige-200'
                          }`}
                        >
                          {allSelected && <Check size={14} />}
                          {category}
                          {selectedCount > 0 && (
                            <span className={`inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full text-xs ${
                              allSelected ? 'bg-white/20 text-white' : 'bg-brand-700 text-white'
                            }`}>
                              {selectedCount}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Section 2: 目标地区 */}
                <div>
                  <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-2">
                    目标地区
                  </h3>
                  <p className="font-sans text-sm font-light text-beige-600 mb-4">
                    选择目标地区（点击切换该地区所有城市）
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(REGION_CITY_MAP).map(([region, cities]) => {
                      const selectedInRegion = cities.filter((c) => formData.selectedCities.includes(c));
                      const allSelected = cities.length > 0 && selectedInRegion.length === cities.length;
                      const partial = selectedInRegion.length > 0 && selectedInRegion.length < cities.length;
                      return (
                        <button
                          key={region}
                          type="button"
                          onClick={() => selectAllCitiesInRegion(region)}
                          className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-sans text-sm font-light transition-all duration-200 ${
                            allSelected
                              ? 'bg-brand-700 text-white shadow-sm'
                              : partial
                                ? 'bg-brand-700/60 text-white'
                                : 'bg-beige-100 text-beige-700 hover:bg-beige-200'
                          }`}
                        >
                          {allSelected && <Check size={14} />}
                          {region}
                          {selectedInRegion.length > 0 && (
                            <span className={`inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full text-xs ${
                              allSelected ? 'bg-white/20 text-white' : 'bg-brand-700 text-white'
                            }`}>
                              {selectedInRegion.length}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

{/* Section 3: 学校层次 */}
                <div>
                  <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-2">
                    学校层次
                  </h3>
                  <p className="font-sans text-sm font-light text-beige-600 mb-4">
                    选择你倾向的学校层次（可多选）
                  </p>
                  <div className="flex flex-wrap gap-3">
                    {TIERS.map((tier) => (
                      <button
                        key={tier}
                        type="button"
                        onClick={() => toggleTier(tier)}
                        className={`px-4 py-2 rounded-lg font-sans text-sm font-light transition-all duration-200 ${
                          formData.tiers.includes(tier)
                            ? 'bg-brand-700 text-white shadow-sm'
                            : 'bg-beige-100 text-beige-700 hover:bg-beige-200'
                        }`}
                      >
                        {tier}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Section 4: 填报优先级 */}
                <div>
                  <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-2">
                    填报优先级
                  </h3>
                  <p className="font-sans text-sm font-light text-beige-600 mb-4">选择你最看重的因素</p>
                  <div className="grid grid-cols-3 gap-3">
                    {([
                      { value: 'school' as const, label: '院校优先', icon: Building2 },
                      { value: 'major' as const, label: '专业优先', icon: GraduationCap },
                      { value: 'city' as const, label: '城市优先', icon: Map },
                    ]).map(({ value, label, icon: Icon }) => (
                      <button
                        key={value}
                        onClick={() => setFormData((prev) => ({ ...prev, priority: value }))}
                        className={`flex flex-col items-center gap-2 py-4 px-3 rounded-xl transition-all duration-200 ${
                          formData.priority === value
                            ? 'bg-brand-700 text-white shadow-sm'
                            : 'bg-beige-100 text-beige-700 hover:bg-beige-200'
                        }`}
                      >
                        <Icon size={20} />
                        <span className="font-sans text-xs font-light">{label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="ghost" size="lg" onClick={handlePrev}>
                  上一步
                </Button>
                <Button variant="gold" size="lg" onClick={handleNext}>
                  下一步
                </Button>
              </div>
            </motion.div>
          )}



          {/* Step 3: Confirm */}
          {step === 3 && (
            <motion.div
              key="step3"
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="space-y-6"
            >
              <div className="card-premium p-8 md:p-10 space-y-6">
                <h3 className="font-serif text-xl font-normal italic text-brand-900 mb-6">
                  确认信息
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">省份</div>
                    <div className="font-sans text-base font-light text-brand-900">{formData.province}</div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">
                      考试类型
                      {provinceConfig?.exam_mode && (
                        <span className="ml-1">({provinceConfig.exam_mode})</span>
                      )}
                    </div>
                    <div className="font-sans text-base font-light text-brand-900">{formData.examType}</div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">分数</div>
                    <div className="font-sans text-base font-light text-brand-900">{formData.score} 分</div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">位次</div>
                    <div className="font-sans text-base font-light text-brand-900">{Number(formData.rank).toLocaleString()} 名</div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">兴趣方向</div>
                    <div className="font-sans text-base font-light text-brand-900">
                      {formData.selectedInterests.length > 0
                        ? formData.selectedInterests.join('、')
                        : formData.interests.length > 0
                          ? formData.interests.join('、')
                          : '未选择'}
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">目标地区</div>
                    <div className="font-sans text-base font-light text-brand-900">
                      {formData.selectedCities.length > 0
                        ? formData.selectedCities.join('、')
                        : formData.regions.length > 0
                          ? formData.regions.join('、')
                          : '不限'}
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">学校层次</div>
                    <div className="font-sans text-base font-light text-brand-900">
                      {formData.tiers.length > 0 ? formData.tiers.join('、') : '不限'}
                    </div>
                  </div>
                  <div className="p-4 rounded-xl bg-beige-50">
                    <div className="font-mono text-caption-mono text-beige-500 mb-1">优先级</div>
                    <div className="font-sans text-base font-light text-brand-900">
                      {formData.priority === 'school' ? '院校优先' : formData.priority === 'major' ? '专业优先' : '城市优先'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="ghost" size="lg" onClick={handlePrev}>
                  上一步
                </Button>
                <Button variant="gold" size="lg" onClick={handleSubmit}>
                  开始推荐
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
          </div>{/* end left form */}

          {/* Right Sidebar - Tips & Links */}
          <div className="hidden lg:flex flex-col gap-6 w-72 shrink-0">
            <div className="sticky top-32 space-y-6">
              <QuickTips />
              <RelatedLinks />
            </div>
          </div>

        </div>{/* end two-column */}
      </div>
    </div>
  );
}
