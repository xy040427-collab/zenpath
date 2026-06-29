import { motion } from 'framer-motion';
import { Building2, BookOpen, TrendingUp } from 'lucide-react';
import type { VolunteerItem } from '../../types';
import { formatProbability, formatRank, formatMatchScore } from '../../utils/formatters';
import { TIER_COLORS } from '../../utils/constants';

interface RecommendationCardProps {
  item: VolunteerItem;
  index?: number;
}

export default function RecommendationCard({ item, index = 0 }: RecommendationCardProps) {
  const tierColor = TIER_COLORS[item.tier];

  return (
    <motion.div
      className="card-premium p-6 flex flex-col"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
      whileHover={{ y: -4 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Building2 size={14} className="text-beige-500 shrink-0" />
            <h4 className="font-serif text-lg font-normal text-brand-900 truncate">
              {item.schoolName}
            </h4>
          </div>
          <div className="flex items-center gap-2">
            <BookOpen size={13} className="text-beige-500 shrink-0" />
            <span className="font-sans text-sm font-light text-ink truncate">
              {item.majorName}
            </span>
          </div>
        </div>
        <span
          className={`shrink-0 text-[10px] font-mono uppercase tracking-[0.15em] px-3 py-1 rounded-full ${tierColor.bg} ${tierColor.text}`}
        >
          {item.tier}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{formatProbability(item.probability)}</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">录取率</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{formatRank(item.expectedRank)}</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">预测位次</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-beige-50">
          <div className="font-mono text-sm font-medium text-brand-900">{formatMatchScore(item.matchScore)}</div>
          <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-beige-600 mt-0.5">匹配度</div>
        </div>
      </div>

      {/* Reason */}
      {item.reason && (
        <div className="flex items-start gap-2 mt-auto pt-3 border-t border-stone">
          <TrendingUp size={13} className="text-accent-gold mt-0.5 shrink-0" />
          <p className="font-sans text-xs font-light text-beige-700 leading-relaxed">{item.reason}</p>
        </div>
      )}
    </motion.div>
  );
}
