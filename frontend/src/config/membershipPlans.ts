/**
 * 择境 ZENPATH 会员方案配置
 * 四档：免费版 / 基础版 / 进阶版 / 尊享版
 * 统一年订阅制（365天有效期）
 */

export type PlanType = 'free' | 'basic' | 'advanced' | 'premium';
export type BillingCycle = 'free' | 'year';

export interface MembershipPlan {
  name: string;
  subtitle: string;
  price: number;
  originalPrice: number;
  billingCycle: BillingCycle;
  durationDays: number | null;
  features: string[];
  cta: string;
  suitableFor: string;
  limitation?: string;
  /** 功能权限控制 */
  maxAiMatches: number | null;        // null = unlimited
  maxVolunteerItems: number | null;   // null = unlimited
  maxSavedPlans: number | null;
  canExport: boolean;
  canGenerateFullReport: boolean;
  canViewGroupMajorDetails: boolean;
  canViewAdjustmentRisk: boolean;
  canViewMajorMatchRate: boolean;
  canUseDeepAIQA: boolean;
  canCompareMultiPlan: boolean;
  canUseHumanReview: boolean;
  humanReviewCount: number;
  consultationMinutes: number;
  finalCheckCount: number;
  /** CHSI RAG 功能权限 */
  canViewRagSchoolProfile: boolean;
  canViewRagAdmissionPolicy: boolean;
  canViewRagDeepAnalysis: boolean;
  canViewRagReportSection: boolean;
  /** 锁定提示 */
  lockedLabel?: string;
}

export const MEMBERSHIP_PLANS: Record<PlanType, MembershipPlan> = {
  free: {
    name: '免费版',
    subtitle: '快速了解志愿填报方向',
    price: 0,
    originalPrice: 0,
    billingCycle: 'free',
    durationDays: null,
    features: [
      'AI 院校智能匹配：限 5 所',
      '基础录取机会评估',
      '基础院校数据查询',
      '志愿填报基础指南',
      '志愿表预览：限 10 个志愿',
      '基础院校简介（CHSI 官方资料）',
    ],
    cta: '免费开始',
    suitableFor: '适合：先了解自己大概能报什么',
    limitation: '免费版仅提供初步参考，不包含完整志愿表、专业组内专业分析和调剂风险评估。',
    maxAiMatches: 5,
    maxVolunteerItems: 10,
    maxSavedPlans: 1,
    canExport: false,
    canGenerateFullReport: false,
    canViewGroupMajorDetails: false,
    canViewAdjustmentRisk: false,
    canViewMajorMatchRate: false,
    canUseDeepAIQA: false,
    canCompareMultiPlan: false,
    canUseHumanReview: false,
    humanReviewCount: 0,
    consultationMinutes: 0,
    finalCheckCount: 0,
    canViewRagSchoolProfile: true,
    canViewRagAdmissionPolicy: false,
    canViewRagDeepAnalysis: false,
    canViewRagReportSection: false,
  },

  basic: {
    name: '基础版',
    subtitle: '生成一份完整可用的志愿方案',
    price: 49,
    originalPrice: 99,
    billingCycle: 'year',
    durationDays: 365,
    features: [
      'AI 院校智能匹配：不限量',
      '录取机会评估',
      '冲稳保策略分析',
      '完整志愿表生成',
      '基础个性化分析报告',
      '支持导出 PDF / Excel',
      '会员期内可保存 3 套方案',
      '基础院校介绍 + 招生章程（CHSI 官方资料）',
      '365 天有效',
    ],
    cta: '选择基础版',
    suitableFor: '适合：想快速生成完整志愿表的考生',
    maxAiMatches: null,
    maxVolunteerItems: null,
    maxSavedPlans: 3,
    canExport: true,
    canGenerateFullReport: true,
    canViewGroupMajorDetails: false,
    canViewAdjustmentRisk: false,
    canViewMajorMatchRate: false,
    canUseDeepAIQA: false,
    canCompareMultiPlan: false,
    canUseHumanReview: false,
    humanReviewCount: 0,
    consultationMinutes: 0,
    finalCheckCount: 0,
    canViewRagSchoolProfile: true,
    canViewRagAdmissionPolicy: true,
    canViewRagDeepAnalysis: false,
    canViewRagReportSection: false,
  },

  advanced: {
    name: '进阶版',
    subtitle: '看清专业组与调剂风险',
    price: 129,
    originalPrice: 199,
    billingCycle: 'year',
    durationDays: 365,
    features: [
      '全部基础版功能',
      '专业倾向测评',
      '专业组内专业明细分析',
      '目标专业命中度分析',
      '调剂风险评估',
      '专业就业前景解读',
      '院校专业组风险提醒',
      '多方案对比优化',
      'AI 深度答疑',
      '深度个性化分析报告',
      'CHSI 官方资料深度解读（章程风险、专业组解释）',
      '365 天有效',
    ],
    cta: '选择进阶版',
    suitableFor: '适合：重视专业选择、担心被调剂的考生',
    maxAiMatches: null,
    maxVolunteerItems: null,
    maxSavedPlans: null,
    canExport: true,
    canGenerateFullReport: true,
    canViewGroupMajorDetails: true,
    canViewAdjustmentRisk: true,
    canViewMajorMatchRate: true,
    canUseDeepAIQA: true,
    canCompareMultiPlan: true,
    canUseHumanReview: false,
    humanReviewCount: 0,
    consultationMinutes: 0,
    finalCheckCount: 0,
    canViewRagSchoolProfile: true,
    canViewRagAdmissionPolicy: true,
    canViewRagDeepAnalysis: true,
    canViewRagReportSection: true,
  },

  premium: {
    name: '尊享版',
    subtitle: '人工复核你的最终志愿方案',
    price: 399,
    originalPrice: 599,
    billingCycle: 'year',
    durationDays: 365,
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
    cta: '预约尊享版',
    suitableFor: '适合：需要人工把关、希望降低决策焦虑的家庭',
    limitation: '人工复核服务即将开放，当前可先选择进阶版生成深度方案。',
    maxAiMatches: null,
    maxVolunteerItems: null,
    maxSavedPlans: null,
    canExport: true,
    canGenerateFullReport: true,
    canViewGroupMajorDetails: true,
    canViewAdjustmentRisk: true,
    canViewMajorMatchRate: true,
    canUseDeepAIQA: true,
    canCompareMultiPlan: true,
    canUseHumanReview: true,
    humanReviewCount: 1,
    consultationMinutes: 30,
    finalCheckCount: 1,
    lockedLabel: '人工服务即将开放',
    canViewRagSchoolProfile: true,
    canViewRagAdmissionPolicy: true,
    canViewRagDeepAnalysis: true,
    canViewRagReportSection: true,
  },
};

/** 会员等级排序权重 */
export const PLAN_ORDER: Record<PlanType, number> = {
  free: 0,
  basic: 1,
  advanced: 2,
  premium: 3,
};

/** 检查是否有某功能的权限 */
export function canAccessFeature(plan: PlanType, feature: keyof MembershipPlan): boolean {
  const p = MEMBERSHIP_PLANS[plan];
  const val = p[feature];
  if (typeof val === 'boolean') return val;
  if (typeof val === 'number') return val > 0;
  return false;
}

/** 获取锁定升级文案 */
export function getLockedMessage(featureName: string, requiredPlan: PlanType): string {
  const plan = MEMBERSHIP_PLANS[requiredPlan];
  return `${featureName} 🔒 ${plan.name}可查看`;
}
