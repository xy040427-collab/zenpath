import type { NavLink, StatsData, FeatureItem, StepItem, FAQItem, PricingTier } from '../types';

export const BRAND = {
  name: '择境',
  nameFull: '择境 ZENPATH',
  tagline: '择善境，行远路',
  taglineFull: '择善境，行远路 — AI 智能高考志愿填报系统',
  description: 'AI 智能高考志愿填报系统，为你生成有依据的冲稳保方案',
  year: '2026',
};

export const NAV_LINKS: NavLink[] = [
  { label: '首页', href: '/' },
  { label: '志愿评估', href: '/calculator' },
  { label: '价格方案', href: '/pricing' },
  { label: '院校列表', href: '/volunteer-list' },
  { label: 'AI 问答', href: '/chat' },
  { label: '分析报告', href: '/report' },
];

export const STATS: StatsData = {
  schools: 3000,
  majors: 700,
  provinces: 31,
  years: 10,
};

export const STATS_DISPLAY = [
  { value: '3000+', label: '院校数据' },
  { value: '700+', label: '专业覆盖' },
  { value: '31', label: '省市区' },
  { value: '10年', label: '录取数据' },
];

export const STEPS: StepItem[] = [
  {
    step: 1,
    icon: 'ClipboardCheck',
    title: '输入信息',
    description: '填写高考分数、排名、选科信息和地域偏好，让系统了解你的基本情况。',
  },
  {
    step: 2,
    icon: 'BrainCircuit',
    title: 'AI 分析',
    description: '基于十年录取数据和 AI 算法，智能分析你的分数匹配度与录取概率。',
  },
  {
    step: 3,
    icon: 'FileOutput',
    title: '生成方案',
    description: '获取专属冲稳保志愿方案，每个推荐都有数据支撑和详细分析报告。',
  },
];

export const FEATURES: FeatureItem[] = [
  {
    icon: 'ScrollText',
    title: '智能志愿填报',
    description: '基于 AI 算法和十年录取数据，自动生成个性化冲稳保志愿方案，每个推荐都有数据支撑。',
  },
  {
    icon: 'LineChart',
    title: '数据可视化',
    description: '多维度图表呈现录取趋势、概率分布和院校对比，让数据一目了然，决策更科学。',
  },
  {
    icon: 'BookMarked',
    title: '院校专业库',
    description: '涵盖全国 3000+ 院校和 700+ 专业详细信息，包括历年分数线、就业前景和学科评估。',
  },
  {
    icon: 'Globe',
    title: '31省全覆盖',
    description: '支持全国 31 个省市区高考数据，适配新高考改革各省选科模式和批次设置。',
  },
  {
    icon: 'ShieldCheck',
    title: '权威数据源',
    description: '数据来源于教育部官方发布和各省考试院，经过严格校验，确保准确可靠。',
  },
  {
    icon: 'MessageSquareText',
    title: 'AI 智能问答',
    description: '随时咨询 AI 志愿顾问，获取院校专业解读、志愿策略建议和个性化答疑。',
  },
];

export const FAQS: FAQItem[] = [
  {
    id: '1',
    question: '择境 ZENPATH 如何保障数据准确性？',
    answer: '择境的所有数据均来源于教育部官方发布和各省教育考试院公开数据，经过多轮交叉校验和人工审核。我们每年在高考录取结束后第一时间更新最新数据，确保信息的时效性和准确性。',
    category: '产品',
  },
  {
    id: '2',
    question: 'AI 生成的志愿方案靠谱吗？',
    answer: '我们的 AI 模型基于十年录取大数据和机器学习算法训练，综合考虑分数、位次、招生计划变化、大小年波动等多种因素。但最终志愿方案仍需结合个人实际情况，建议将 AI 方案作为重要参考而非唯一依据。',
    category: '产品',
  },
  {
    id: '3',
    question: '哪些省份和考试类型支持？',
    answer: '择境全面支持全国 31 个省市区，涵盖新高考"3+3""3+1+2"模式和传统文理分科。无论你来自哪个省份，系统都会根据当地政策和数据为你生成适配方案。',
    category: '产品',
  },
  {
    id: '4',
    question: '付费方案和免费方案有什么区别？',
    answer: '免费版提供快速了解志愿填报方向，AI匹配限5所、志愿表预览限10个。基础版（¥49/年）生成完整志愿表、冲稳保策略分析和可导出报告。进阶版（¥129/年）额外提供专业组内专业明细、调剂风险评估和AI深度答疑。尊享版（¥399/年）包含人工方案复核和一对一咨询。所有付费版均为年订阅制，365天有效。',
    category: '价格',
  },
  {
    id: '5',
    question: '如何理解冲稳保的划分逻辑？',
    answer: '系统根据你的分数和位次，结合历年录取数据计算录取概率。"冲刺"指录取概率在 30%-50% 之间的院校，"稳妥"指 50%-80% 概率，"保底"指 80% 以上概率。划分会考虑招生计划变化等其他因素。',
    category: '产品',
  },
  {
    id: '6',
    question: '付款后可以退款吗？',
    answer: '我们提供 7 天无理由退款保证。如果你对方案质量不满意，可以在购买后 7 天内联系客服申请全额退款。我们将第一时间处理。',
    category: '价格',
  },
  {
    id: '7',
    question: '支持手机端使用吗？',
    answer: '择境采用响应式设计，完美支持手机、平板和电脑端访问。无论你使用什么设备，都能获得流畅的使用体验。建议在电脑端查看详细报告和图表，获得最佳体验。',
    category: '产品',
  },
  {
    id: '8',
    question: '数据多久更新一次？',
    answer: '每年高考录取工作结束后，各省数据会在官方公布后的 48 小时内更新完毕。招生计划等数据会在高考前根据各省发布的招生章程实时更新。',
    category: '产品',
  },
];

export const PRICING_TIERS: PricingTier[] = [
  {
    id: 'free',
    name: '免费版',
    price: 0,
    description: '快速了解志愿填报方向',
    features: [
      'AI 院校智能匹配（限5所）',
      '基础录取机会评估',
      '基础院校数据查询',
      '志愿填报基础指南',
      '志愿表预览（限10个志愿）',
      '基础院校简介（CHSI 官方资料）',
    ],
    badge: '免费',
  },
  {
    id: 'basic',
    name: '基础版',
    price: 49,
    originalPrice: 99,
    billingCycle: 'year',
    description: '生成一份完整可用的志愿方案',
    features: [
      'AI 院校智能匹配（不限量）',
      '录取机会评估',
      '冲稳保策略分析',
      '完整志愿表生成',
      '基础个性化分析报告',
      '支持导出 PDF / Excel',
      '会员期内可保存 3 套方案',
      '基础院校介绍 + 招生章程（CHSI 官方资料）',
      '365 天有效',
    ],
    isPopular: false,
    badge: '推荐',
  },
  {
    id: 'advanced',
    name: '进阶版',
    price: 129,
    originalPrice: 199,
    billingCycle: 'year',
    description: '看清专业组与调剂风险',
    features: [
      '全部基础版功能',
      '专业倾向测评',
      '专业组内专业明细分析',
      '目标专业命中度分析',
      '调剂风险评估',
      '专业就业前景解读',
      'AI 深度答疑',
      '多方案对比优化',
      'CHSI 官方资料深度解读（章程风险、专业组解释）',
      '365 天有效',
    ],
    badge: '进阶',
  },
  {
    id: 'premium',
    name: '尊享版',
    price: 399,
    originalPrice: 599,
    billingCycle: 'year',
    description: '人工复核你的最终志愿方案',
    features: [
      '全部进阶版功能',
      '人工志愿方案复核 1 次',
      '一对一咨询 30 分钟',
      '志愿方案深度优化',
      '填报前最终检查 1 次',
      '录取结果跟踪提醒',
      '大学入学建议',
      'CHSI 官方资料深度解读 + 人工复核入口',
      '365 天有效',
    ],
    isPopular: true,
    badge: '尊享',
  },
];

export const LIVE_DOT_CLASS = 'inline-block w-[6px] h-[6px] rounded-full bg-accent-gold animate-[pulse-dot_2s_ease-in-out_infinite]';

export const TIER_COLORS = {
  '冲刺': { text: 'text-accent-ruby', bg: 'bg-accent-ruby/10', border: 'border-accent-ruby/30', dot: 'bg-accent-ruby' },
  '稳妥': { text: 'text-accent-gold', bg: 'bg-accent-gold/10', border: 'border-accent-gold/30', dot: 'bg-accent-gold' },
  '保底': { text: 'text-accent-teal', bg: 'bg-accent-teal/10', border: 'border-accent-teal/30', dot: 'bg-accent-teal' },
  '不推荐': { text: 'text-gray-500', bg: 'bg-gray-100', border: 'border-gray-200', dot: 'bg-gray-400' },
} as const;

export const API_BASE = '/api/v1';
