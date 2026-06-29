import { motion } from "framer-motion";
import { FC } from "react";

interface RecommendationPreviewProps {
  score: number;
  rank: number;
  matchRate: number;
  rushCount: number;
  stableCount: number;
  safeCount: number;
  className?: string;
}

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

const RecommendationPreview: FC<RecommendationPreviewProps> = ({
  score,
  rank,
  matchRate,
  rushCount,
  stableCount,
  safeCount,
  className = "",
}) => {
  const gaugeCircumference = 2 * Math.PI * 24;
  const gaugeOffset = gaugeCircumference - (matchRate / 100) * gaugeCircumference;

  return (
    <div className={`space-y-4 ${className}`}>
      <motion.h3
        className="font-serif text-lg text-[#1A2E22]"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={0}
      >
        快速匹配
      </motion.h3>

      <motion.div
        className="card-premium p-4"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={1}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="text-center">
            <p className="font-sans text-xs text-[#4A8A7A]">分数</p>
            <p className="font-serif text-2xl font-semibold text-[#1A2E22]">
              {score}
            </p>
          </div>
          <div className="relative flex items-center justify-center">
            <svg width="60" height="60" className="-rotate-90">
              <circle
                cx="30"
                cy="30"
                r="24"
                fill="none"
                stroke="#EDE6D8"
                strokeWidth="4"
              />
              <circle
                cx="30"
                cy="30"
                r="24"
                fill="none"
                stroke="#C4A45C"
                strokeWidth="4"
                strokeDasharray={gaugeCircumference}
                strokeDashoffset={gaugeOffset}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute font-sans text-xs font-semibold text-[#1A2E22]">
              {matchRate}%
            </span>
          </div>
          <div className="text-center">
            <p className="font-sans text-xs text-[#4A8A7A]">位次</p>
            <p className="font-serif text-lg font-semibold text-[#1A2E22]">
              {rank.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {[
            { label: "冲刺", count: rushCount, color: "bg-[#A84A3A]" },
            { label: "稳妥", count: stableCount, color: "bg-[#4A8A7A]" },
            { label: "保底", count: safeCount, color: "bg-[#C4B8A8]" },
          ].map((tier) => (
            <div
              key={tier.label}
              className="flex-1 text-center p-2 rounded-xl bg-[#F5F0E8]"
            >
              <div className="flex items-center justify-center gap-1 mb-0.5">
                <span className={`w-2 h-2 rounded-full ${tier.color}`} />
                <span className="font-sans text-xs text-[#2D4A3E]">
                  {tier.label}
                </span>
              </div>
              <span className="font-serif text-base font-semibold text-[#1A2E22]">
                {tier.count}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={2}
      >
        <a
          href="/calculator"
          className="block w-full text-center py-2.5 rounded-xl bg-[#C4A45C] text-white font-sans text-sm font-medium hover:bg-[#b3944d] transition-colors"
        >
          查看完整方案
        </a>
      </motion.div>
    </div>
  );
};

export default RecommendationPreview;
