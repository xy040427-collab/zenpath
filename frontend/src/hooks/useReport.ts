import { useState, useCallback } from 'react';
import type { Recommendation, Preference } from '../types';
import { getRecommendations } from '../services/recommendation';

export function useReport() {
  const [report, setReport] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateReport = useCallback(async (preference: Preference) => {
    setLoading(true);
    setError(null);
    try {
      // Call backend real algorithm
      const result = await getRecommendations({
        score: preference.score.total,
        rank: preference.rank,
        province: preference.province,
        examType: preference.examType,
      });

      const report: Recommendation = {
        id: result.id,
        userId: 'user_1',
        score: preference.score,
        rank: preference.rank,
        province: preference.province,
        createdAt: new Date().toISOString(),
        rush: result.rush,
        stable: result.stable,
        safe: result.safe,
        notRecommended: result.notRecommended,
        summary: (result.summary?.strategy as string) || '基于你的分数和位次，系统已生成冲稳保方案。',
        matchRate: (result.summary?.match_rate as number) || 85,
        totalSchools: (result.summary?.total_candidates as number) || 0,
        totalMajors: 0,
      };
      setReport(report);
      return report;
    } catch (err) {
      const message = err instanceof Error ? err.message : '报告生成失败';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearReport = useCallback(() => {
    setReport(null);
    setError(null);
  }, []);

  return { report, loading, error, generateReport, clearReport };
}
