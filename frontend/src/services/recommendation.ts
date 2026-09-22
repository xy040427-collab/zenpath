import api from './api';
import type { VolunteerItem, School, Major } from '../types';

/** Call NEW SQL-RAG recommendation API with real database data */
export async function getRecommendations(params: {
  score: number;
  rank: number;
  province: string;
  examType: string;
  interests?: string[];
  regions?: string[];
  priority?: string;
}): Promise<{
  rush: VolunteerItem[];
  stable: VolunteerItem[];
  safe: VolunteerItem[];
  notRecommended: VolunteerItem[];
  summary: Record<string, unknown>;
  id: string;
}> {
  const subjectStr = (params.examType === '物理' || params.examType === '物理类') ? '物化生' : '史地政';
  
  // Build rich natural-language query including all user preferences
  const parts = [`${params.province}考生 ${params.score}分 位次${params.rank} ${subjectStr}`];
  
  if (params.interests && params.interests.length > 0) {
    parts.push(`想学${params.interests.join('、')}`);
  }
  if (params.regions && params.regions.length > 0) {
    const regionStr = params.regions.length <= 3 
      ? params.regions.join('、')
      : params.regions.slice(0, 3).join('、') + '等';
    parts.push(`想去${regionStr}`);
  }
  if (params.priority) {
    parts.push(`${params.priority}一点`);
  }
  
  const message = parts.join(' ');

  const { data } = await api.post('/ai/gaokao/recommend', { message });

  console.log('[DEBUG] API response keys:', Object.keys(data));
  console.log('[DEBUG] total_count:', data.total_count);
  console.log('[DEBUG] byRisk keys:', Object.keys(data.recommendations_by_risk || {}));

  const byRisk = data.recommendations_by_risk || {};

  // Map risk levels: 保→safe, 稳→stable, 冲→rush
  const rushItems: VolunteerItem[] = [];
  const stableItems: VolunteerItem[] = [];
  const safeItems: VolunteerItem[] = [];

  for (const [riskLevel, group] of Object.entries(byRisk) as [string, any][]) {
    const items = group?.items || [];
    for (const item of items) {
      const mapped = mapFromNewAPI(item, riskLevel);
      if (riskLevel === '冲') {
        rushItems.push(mapped);
      } else if (riskLevel === '稳') {
        stableItems.push(mapped);
      } else if (riskLevel === '保') {
        safeItems.push(mapped);
      }
    }
  }

  // Compute summary stats
  const totalItems = rushItems.length + stableItems.length + safeItems.length;
  console.log('[DEBUG] Mapped items - rush:', rushItems.length, 'stable:', stableItems.length, 'safe:', safeItems.length);
  const allProbs = [...rushItems, ...stableItems, ...safeItems].map(i => i.probability).filter(p => p > 0);
  const avgProb = allProbs.length > 0
    ? Math.round((allProbs.reduce((a, b) => a + b, 0) / allProbs.length) * 100)
    : 85;

  return {
    id: `rec-${Date.now()}`,
    summary: {
      total_candidates: data.total_count || totalItems,
      rush_count: rushItems.length,
      stable_count: stableItems.length,
      safe_count: safeItems.length,
      match_rate: avgProb,
      warnings: data.warnings || [],
      summary_text: data.summary || '',
      exam_config: data.exam_config || {},
      parsed_profile: data.parsed_profile || {},
      data_coverage: data.data_coverage || null,
      rag_summary: data.rag_summary || null,
    },
    rush: rushItems,
    stable: stableItems,
    safe: safeItems,
    notRecommended: [],
  };
}

/** Map new API response item to existing VolunteerItem type */
function mapFromNewAPI(item: Record<string, unknown>, riskLevel: string): VolunteerItem {
  const rankAnalysis = (item.rank_analysis || {}) as Record<string, unknown>;
  const schoolName = (item.school_name || '') as string;
  const majorName = (item.major_name || '') as string;

  return {
    id: `${schoolName}-${majorName}`,
    schoolId: '',
    schoolName,
    schoolLogo: (item.school_slug || '') as string,
    majorId: '',
    majorName,
    majorCategory: '',
    tier: riskLevel === '保' ? '保底' : riskLevel === '稳' ? '稳妥' : riskLevel === '冲' ? '冲刺' : '不推荐',
    probability: ((item.probability ?? 0) as number) / 100,
    matchScore: (item.major_relevance ?? 0) as number,
    expectedRank: (item.latest_min_rank ?? rankAnalysis.best_year_rank ?? 0) as number,
    reason: (item.algorithm_reason || '') as string,
    year: (item.latest_year ?? 2025) as number,
    isRecommended: riskLevel !== '不推荐',
    minScore: item.latest_min_score as number | undefined,
    avgScore: item.latest_min_score as number | undefined,
    minRank: item.latest_min_rank as number | undefined,
    avgRank: rankAnalysis.avg_rank as number | undefined,
    maxRank: rankAnalysis.worst_year_rank as number | undefined,
    maxScore: undefined,
    historicalData: rankAnalysis.historical_ranks as number[] | undefined,
    // Additional fields from new API
    city: item.city as string | undefined,
    is_sino_foreign: item.is_sino_foreign as boolean | undefined,
    plan_count: item.plan_count as number | undefined,
    data_years: item.data_years as number | undefined,
    rag_summary: item.rag_summary as string | undefined,
  } as VolunteerItem;
}

export async function getSchools(params: {
  page?: number;
  pageSize?: number;
  province?: string;
  type?: string;
  level?: string;
  search?: string;
}): Promise<{ items: School[]; total: number }> {
  const { data } = await api.get('/schools', { params });
  return data;
}

export async function getMajors(params: {
  page?: number;
  pageSize?: number;
  category?: string;
  search?: string;
}): Promise<{ items: Major[]; total: number }> {
  const { data } = await api.get('/majors', { params });
  return data;
}

export async function getSchoolDetail(id: string): Promise<School> {
  const { data } = await api.get(`/schools/${id}`);
  return data.data;
}

// ═══════════════════════════════════════════
//  Jiangsu Recommendation API (v2)
// ═══════════════════════════════════════════
import axios from 'axios';
import type { JiangsuRecommendResponse } from '../types';

const pendingJiangsu = new Map<string, Promise<JiangsuRecommendResponse>>();

export function getJiangsuRecommendations(params: {
  year: number;
  subject_type: string;
  score: number;
  rank?: number;
  selected_subjects: string[];
  preferred_majors: string[];
  preferred_cities: string[];
  preferred_tiers?: string[];
  strategy: string;
  top_n: number;
}): Promise<JiangsuRecommendResponse> {
  // Share only in-flight identical requests (React StrictMode mounts twice).
  // Completed responses are not cached; a later deliberate retry is fresh.
  const key = JSON.stringify(params);
  const existing = pendingJiangsu.get(key);
  if (existing) return existing;
  const request = axios.post<JiangsuRecommendResponse>(
    '/api/gaokao/jiangsu/recommend', params,
    { headers: { 'Content-Type': 'application/json' }, timeout: 60000 },
  ).then(({ data }) => data).finally(() => pendingJiangsu.delete(key));
  pendingJiangsu.set(key, request);
  return request;
}
