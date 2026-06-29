import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BRAND } from '../../utils/constants';

const productLinks = [
  { label: '志愿评估', href: '/calculator' },
  { label: '价格方案', href: '/pricing' },
  { label: '院校列表', href: '/volunteer-list' },
  { label: 'AI 问答', href: '/chat' },
];

const supportLinks = [
  { label: '使用指南', href: '#' },
  { label: '常见问题', href: '#faq' },
  { label: '数据来源', href: '#' },
  { label: '联系我们', href: '#' },
];

const legalLinks = [
  { label: '服务条款', href: '#' },
  { label: '隐私政策', href: '#' },
  { label: '数据安全', href: '#' },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function Footer() {
  const [email, setEmail] = useState('');

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Decorative only
    setEmail('');
  };

  return (
    <footer className="bg-[#1A2E22] relative">
      {/* Gold top accent border */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#C4A45C]/50 to-transparent" />

      <motion.div
        className="max-w-6xl mx-auto px-6 lg:px-8 py-16 md:py-20"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
      >
        {/* Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 md:gap-8">
          {/* Brand */}
          <motion.div className="col-span-2 md:col-span-1" variants={itemVariants}>
            <Link to="/" className="flex items-center gap-3 mb-6 group">
              <motion.div
                className="w-9 h-9 rounded-full overflow-hidden"
                animate={{ y: [0, -2, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              >
                <img src="/favicon.png" alt="择境" className="w-full h-full object-cover" />
              </motion.div>
              <div>
                <span className="font-serif text-lg font-light text-white">{BRAND.name}</span>
                <div className="font-mono text-[9px] uppercase tracking-[0.3em] text-white/40">
                  ZENPATH
                </div>
              </div>
            </Link>
            <p className="font-serif text-sm italic text-white/50 leading-relaxed mb-4">
              {BRAND.tagline}
            </p>
            <p className="font-sans text-xs font-light text-white/40 leading-relaxed">
              AI 智能高考志愿填报系统
              <br />
              让每一个志愿选择都有依据
            </p>
          </motion.div>

          {/* Product */}
          <motion.div variants={itemVariants}>
            <h4 className="font-mono text-caption-mono text-accent-gold mb-5">产品</h4>
            <ul className="space-y-3">
              {productLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="font-sans text-sm font-light text-white/60 hover:text-white transition-colors duration-300 inline-block hover:translate-x-1"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Support */}
          <motion.div variants={itemVariants}>
            <h4 className="font-mono text-caption-mono text-accent-gold mb-5">支持</h4>
            <ul className="space-y-3">
              {supportLinks.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="font-sans text-sm font-light text-white/60 hover:text-white transition-colors duration-300 inline-block hover:translate-x-1"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Legal */}
          <motion.div variants={itemVariants}>
            <h4 className="font-mono text-caption-mono text-accent-gold mb-5">法律</h4>
            <ul className="space-y-3">
              {legalLinks.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="font-sans text-sm font-light text-white/60 hover:text-white transition-colors duration-300 inline-block hover:translate-x-1"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Contact / Newsletter */}
          <motion.div variants={itemVariants}>
            <h4 className="font-mono text-caption-mono text-accent-gold mb-5">联系</h4>
            <p className="font-sans text-sm font-light text-white/60 leading-relaxed mb-4">
              客服邮箱
              <br />
              <a href="mailto:hello@zenpath.cn" className="text-white/80 hover:text-white transition-colors">
                hello@zenpath.cn
              </a>
            </p>
            <p className="font-sans text-xs font-light text-white/40 mb-6">
              工作日 9:00 - 18:00
            </p>
            {/* Newsletter signup */}
            <form onSubmit={handleNewsletterSubmit} className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="订阅更新"
                className="flex-1 px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-white/70 text-xs font-sans placeholder:text-white/30 focus:outline-none focus:border-accent-gold/50 transition-colors"
              />
              <button
                type="submit"
                className="px-3 py-2 rounded-lg bg-accent-gold text-brand-900 text-[10px] font-mono uppercase tracking-widest hover:bg-accent-gold-dark transition-colors"
              >
                订阅
              </button>
            </form>
          </motion.div>
        </div>

        {/* Divider with gold accent */}
        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-10" />

        {/* Copyright bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="font-sans text-xs font-light text-white/40 order-2 md:order-1">
            &copy; {new Date().getFullYear()} {BRAND.nameFull}. All rights reserved.
          </p>
          <div className="flex items-center gap-6 order-1 md:order-2">
            {productLinks.slice(0, 3).map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/30 hover:text-white/60 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </motion.div>
    </footer>
  );
}
