import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { FC } from "react";

interface RelatedLinksProps {
  className?: string;
}

const links = [
  { href: "/calculator", label: "志愿评估工具" },
  { href: "/pricing", label: "查看价格方案" },
  { href: "/volunteer-list", label: "浏览院校列表" },
  { href: "/faq", label: "常见问题" },
];

const fadeInUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.35 },
  }),
};

const RelatedLinks: FC<RelatedLinksProps> = ({ className = "" }) => {
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
        相关链接
      </motion.h3>

      <div className="space-y-1">
        {links.map((link, i) => (
          <motion.div
            key={link.href}
            variants={fadeInUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={i + 1}
          >
            <a
              href={link.href}
              className="card-premium flex items-center justify-between px-4 py-2.5 hover:bg-[#F5F0E8] transition-colors group"
            >
              <span className="font-sans text-sm text-[#2D4A3E] group-hover:text-[#1A2E22] transition-colors">
                {link.label}
              </span>
              <ChevronRight className="w-4 h-4 text-[#C4B8A8] group-hover:text-[#4A8A7A] transition-colors" />
            </a>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default RelatedLinks;
