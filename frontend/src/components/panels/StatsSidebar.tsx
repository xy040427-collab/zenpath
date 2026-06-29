import { motion } from "framer-motion";
import { FC } from "react";

interface StatsSidebarProps {
  totalSchools: number;
  levelCounts: { level: string; count: number }[];
  provinceCounts: { province: string; count: number }[];
  className?: string;
}

const levelColors: Record<string, string> = {
  "985": "bg-[#A84A3A]",
  "211": "bg-[#C4A45C]",
  "双一流": "bg-[#4A8A7A]",
  "普通": "bg-[#C4B8A8]",
};

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

const StatsSidebar: FC<StatsSidebarProps> = ({
  totalSchools,
  levelCounts,
  provinceCounts,
  className = "",
}) => {
  const maxLevelCount = Math.max(...levelCounts.map((l) => l.count), 1);
  const topProvinces = provinceCounts.slice(0, 10);

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
        数据概览
      </motion.h3>

      <motion.div
        className="card-premium p-4 text-center"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={1}
      >
        <p className="font-sans text-sm text-[#4A8A7A]">院校总数</p>
        <p className="font-serif text-4xl text-[#1A2E22] font-semibold">
          {totalSchools}
        </p>
      </motion.div>

      <motion.div
        className="card-premium p-4 space-y-3"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={2}
      >
        <p className="font-sans text-xs font-medium text-[#2D4A3E]">
          院校层次分布
        </p>
        {levelCounts.map((item, i) => (
          <div key={item.level} className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="font-sans text-[#2D4A3E]">{item.level}</span>
              <span className="font-sans text-[#4A8A7A]">{item.count}</span>
            </div>
            <div className="h-1.5 w-full bg-[#F5F0E8] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  levelColors[item.level] || "bg-[#C4B8A8]"
                }`}
                style={{ width: `${(item.count / maxLevelCount) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </motion.div>

      <motion.div
        className="card-premium p-4 space-y-2"
        variants={fadeInUp}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        custom={3}
      >
        <p className="font-sans text-xs font-medium text-[#2D4A3E]">
          省份分布（Top 10）
        </p>
        {topProvinces.map((item, i) => (
          <div
            key={item.province}
            className="flex justify-between text-xs py-0.5"
          >
            <span className="font-sans text-[#2D4A3E]">{item.province}</span>
            <span className="font-sans text-[#4A8A7A]">{item.count}</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
};

export default StatsSidebar;
