import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface DataCoverageBannerProps {
  coverage: { score_rank: string; admission_lines: string; rag_knowledge: string; warnings: string[] };
}

export default function DataCoverageBanner({ coverage }: DataCoverageBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const hasWarnings = coverage.warnings && coverage.warnings.length > 0;

  const colors: Record<string, string> = {
    available: 'bg-emerald-100 text-emerald-700',
    partial: 'bg-amber-100 text-amber-700',
    missing: 'bg-red-100 text-red-700',
  };
  const labels: Record<string, string> = {
    available: '✅', partial: '⚠️', missing: '❌',
  };

  return (
    <div className="bg-white rounded-xl border border-cream-200 p-4 mb-6">
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-stone-500">数据覆盖:</span>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${colors[coverage.score_rank] || 'bg-stone-100'}`}>
          {labels[coverage.score_rank] || ''} 一分一段表
        </span>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${colors[coverage.admission_lines] || 'bg-stone-100'}`}>
          {labels[coverage.admission_lines] || ''} 投档线
        </span>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${colors[coverage.rag_knowledge] || 'bg-stone-100'}`}>
          {labels[coverage.rag_knowledge] || ''} RAG知识库
        </span>
      </div>

      {hasWarnings && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-xs text-amber-600 hover:text-amber-700 flex items-center gap-1 transition-colors"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {coverage.warnings.length}条数据提示
          </button>
          {expanded && (
            <div className="mt-2 space-y-1">
              {coverage.warnings.map((w: string, i: number) => (
                <p key={i} className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                  ⚠️ {w}
                </p>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
