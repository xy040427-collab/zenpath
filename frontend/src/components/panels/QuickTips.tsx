import { motion } from "framer-motion";
import {
  Lightbulb,
  TrendingUp,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import { FC } from "react";

const tips = [
  {
    icon: Lightbulb,
    text: "选择专业时，建议优先考虑自己的兴趣和学科优势",
  },
  {
    icon: TrendingUp,
    text: "关注近三年录取位次趋势，比分数更稳定可靠",
  },
  {
    icon: ShieldCheck,
    text: "采用冲稳保策略，合理分配志愿梯度降低风险",
  },
  {
    icon: BookOpen,
    text: "仔细阅读目标院校招生章程，了解专业录取规则",
  },
];

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.4 },
  }),
};

const QuickTips: FC = () => {
  return (
    <div className="space-y-4">
      <motion.h3
        className="font-serif text-lg text-[#1A2E22]"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={0}
      >
        填报贴士
      </motion.h3>

      <div className="space-y-2">
        {tips.map((tip, i) => {
          const Icon = tip.icon;
          return (
            <motion.div
              key={i}
              className="card-premium p-3 flex items-start gap-3"
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i + 1}
            >
              <div className="mt-0.5 p-1.5 rounded-lg bg-[#F5F0E8] shrink-0">
                <Icon className="w-4 h-4 text-[#4A8A7A]" />
              </div>
              <p className="font-sans text-sm text-[#2D4A3E] leading-relaxed">
                {tip.text}
              </p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default QuickTips;
