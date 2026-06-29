interface ScoreBadgeProps {
  score: number;
  rank: number;
  className?: string;
}

export default function ScoreBadge({ score, rank, className = '' }: ScoreBadgeProps) {
  return (
    <div className={`inline-flex items-center gap-4 ${className}`}>
      <div className="text-center">
        <div className="font-serif text-4xl font-light text-brand-900 tracking-tight">
          {score}
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-600 mt-1">
          总分
        </div>
      </div>
      <div className="w-px h-12 bg-stone" />
      <div className="text-center">
        <div className="font-mono text-xl font-light text-brand-700">
          {rank >= 10000 ? `${(rank / 10000).toFixed(1)}万` : rank}
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-600 mt-1">
          位次
        </div>
      </div>
    </div>
  );
}
