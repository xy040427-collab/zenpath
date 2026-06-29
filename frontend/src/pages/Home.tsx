import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, Star, Gem, ScrollText, LineChart, BookMarked,
  Globe, ShieldCheck, MessageSquareText, ClipboardCheck, BrainCircuit,
  FileOutput, ChevronDown, ChevronRight, CircleCheckBig, Sprout, Award,
} from 'lucide-react';
import { STATS_DISPLAY, STEPS, FEATURES, FAQS, BRAND } from '../utils/constants';
import Button from '../components/common/Button';

// ============== Counter Animation Hook ==============
function useCountUp(target: number, duration: number = 2, start: boolean = true) {
  const [count, setCount] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (!start || started.current) return;
    started.current = true;
    let frame: number;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = (now - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutExpo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCount(Math.round(eased * target));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [target, duration, start]);

  return count;
}

// ============== Scroll Reveal Wrapper ==============
function ScrollReveal({ children, delay = 0, className = '' }: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.7, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      {children}
    </motion.div>
  );
}

// ============== Section Heading ==============
function SectionHeading({ title, subtitle, light = false }: {
  title: string;
  subtitle?: string;
  light?: boolean;
}) {
  return (
    <div className="text-center mb-16">
      <h2 className={`font-serif text-h2 ${light ? 'text-white' : 'text-brand-900'}`}>
        {title}
      </h2>
      {subtitle && (
        <p className={`font-sans text-lg font-light italic max-w-2xl mx-auto mt-4 ${
          light ? 'text-white/60' : 'text-beige-600'
        }`}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

// ============== Staggered Character Animation ==============
function StaggeredText({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span className={className}>
      {text.split('').map((char, i) => (
        <motion.span
          key={i}
          className="inline-block"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 + i * 0.08, duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          {char === ' ' ? '\u00A0' : char}
        </motion.span>
      ))}
    </span>
  );
}

// ============== Step Connector Line ==============
function StepConnector() {
  return (
    <div className="hidden md:block absolute top-24 left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)]">
      <motion.div
        className="h-px bg-gradient-to-r from-accent-gold/20 via-accent-gold to-accent-gold/20"
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, delay: 0.3, ease: 'easeInOut' }}
        style={{ originX: 0 }}
      />
    </div>
  );
}

// ============== Animated Counter ==============
function AnimatedStat({ value, label, prefix = '' }: { value: string; label: string; prefix?: string }) {
  const [ref, setRef] = useState<HTMLDivElement | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    if (!ref) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); observer.disconnect(); } },
      { threshold: 0.3 }
    );
    observer.observe(ref);
    return () => observer.disconnect();
  }, [ref]);

  const numValue = parseInt(value.replace(/[+\u5e74]/g, ''));
  const suffix = value.includes('+') ? '+' : value.includes('年') ? '年' : '';
  const displayValue = useCountUp(isNaN(numValue) ? 0 : numValue, 2, inView);

  return (
    <div ref={setRef} className="text-center">
      <div className="font-mono text-lg md:text-xl text-white font-light">
        {prefix}{displayValue}{suffix}
      </div>
      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-white/40 mt-1">{label}</div>
    </div>
  );
}

// ============== FAQ Accordion Item ==============
function FAQItem({ faq, isOpen, onClick }: {
  faq: typeof FAQS[0];
  isOpen: boolean;
  onClick: () => void;
}) {
  return (
    <div className="border-b border-[#E0D8CC] last:border-b-0">
      <button
        onClick={onClick}
        className="w-full flex items-center justify-between py-5 px-6 text-left transition-colors hover:bg-beige-50/50 group"
      >
        <span className="font-sans text-base font-light text-brand-900 group-hover:text-brand-700 pr-4">
          {faq.question}
        </span>
        <motion.div
          animate={{ rotate: isOpen ? 45 : 0 }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
        >
          <ChevronRight size={16} className="shrink-0 text-beige-500" />
        </motion.div>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-5">
              <div className="w-12 h-0.5 bg-accent-gold mb-4" />
              <p className="font-sans text-sm font-light text-beige-700 leading-relaxed">
                {faq.answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============== HOME PAGE ==============
export default function Home() {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState<string | null>(null);

  const toggleFaq = (id: string) => {
    setOpenFaq(openFaq === id ? null : id);
  };

  const staggerContainer = {
    hidden: {},
    visible: {
      transition: { staggerChildren: 0.08 },
    },
  };

  const staggerItem = {
    hidden: { opacity: 0, y: 20, x: -8 },
    visible: { opacity: 1, y: 0, x: 0 },
  };

  return (
    <>
      {/* ========== HERO ========== */}
      <section className="gradient-hero min-h-screen flex items-center relative overflow-hidden">
        {/* Ken Burns background */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: 'radial-gradient(circle at 30% 40%, rgba(196,164,92,0.3) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(255,255,255,0.1) 0%, transparent 50%)',
            animation: 'kenBurns 20s ease-in-out infinite alternate',
          }}
        />

        <div className="max-w-6xl mx-auto px-6 lg:px-8 pt-32 pb-20 md:pb-28 relative z-10 w-full">
          {/* Badge */}
          <motion.div
            className="flex items-center justify-center gap-3 mb-8"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6 }}
          >
            <span className="inline-block w-[6px] h-[6px] rounded-full bg-accent-gold animate-[pulse-dot_2s_ease-in-out_infinite]" />
            <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-accent-gold">
              {BRAND.year}高考志愿填报
            </span>
          </motion.div>

          {/* Staggered Character Animation */}
          <h1 className="text-center mb-6">
            <StaggeredText
              text="择善境  行远路"
              className="block font-serif text-h1 font-light text-white tracking-tight leading-[1.15]"
            />
          </h1>

          {/* Tagline - fades in 0.5s later */}
          <motion.p
            className="font-serif text-lg md:text-xl italic text-accent-gold/80 text-center max-w-xl mx-auto mb-10"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0, duration: 0.7 }}
          >
            AI 智能高考志愿填报系统 — 让每一个志愿选择都有依据
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="flex flex-wrap items-center justify-center gap-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3, duration: 0.7 }}
          >
            <Button variant="gold" size="lg" href="/calculator">
              免费开始评估
            </Button>
            <Button variant="outline" size="lg" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>
              了解更多
            </Button>
          </motion.div>

          {/* Stats row with counters */}
          <motion.div
            className="flex flex-wrap items-center justify-center gap-8 md:gap-12 mt-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6, duration: 0.7 }}
          >
            {STATS_DISPLAY.map((stat, i) => (
              <AnimatedStat key={i} value={stat.value} label={stat.label} />
            ))}
          </motion.div>

          {/* Scroll cue */}
          <motion.div
            className="flex justify-center mt-16"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.0, duration: 0.7 }}
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >
              <ChevronDown size={20} className="text-white/30" />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ========== HOW IT WORKS ========== */}
      <section id="how-it-works" className="gold-section py-28 md:py-36">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <ScrollReveal>
            <SectionHeading
              title="三步获取你的专属方案"
              subtitle="简单三步，AI 为你生成科学可依的志愿填报方案"
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-10 relative">
            <StepConnector />
            {STEPS.map((step, i) => {
              const IconComponent =
                step.icon === 'ClipboardCheck'
                  ? ClipboardCheck
                  : step.icon === 'BrainCircuit'
                  ? BrainCircuit
                  : FileOutput;

              return (
                <ScrollReveal key={step.step} delay={i * 0.15}>
                  <motion.div
                    className="card-premium p-8 md:p-10 text-center relative"
                    whileHover={{ y: -4, boxShadow: '0 8px 32px rgba(26,46,34,0.08)' }}
                    transition={{ duration: 0.3 }}
                  >
                    {/* Step number */}
                    <motion.div
                      className="w-14 h-14 rounded-full bg-[#E8DCC0] flex items-center justify-center mx-auto mb-6"
                      whileInView={{ scale: [1, 1.1, 1] }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.5, type: 'spring', stiffness: 200 }}
                    >
                      <IconComponent size={24} className="text-[#A8883C]" />
                    </motion.div>
                    <div className="font-mono text-caption-mono text-accent-gold mb-3">
                      STEP 0{step.step}
                    </div>
                    <h3 className="font-serif text-lg font-normal italic text-brand-900 mb-3">
                      {step.title}
                    </h3>
                    <p className="font-sans text-sm font-light text-beige-700 leading-relaxed">
                      {step.description}
                    </p>
                  </motion.div>
                </ScrollReveal>
              );
            })}
          </div>
        </div>
      </section>

      {/* ========== FEATURES ========== */}
      <section className="py-28 md:py-36 bg-white">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <ScrollReveal>
            <SectionHeading
              title="核心功能"
              subtitle="六大核心功能，为你的志愿填报保驾护航"
            />
          </ScrollReveal>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
          >
            {FEATURES.map((feature, i) => {
              const IconMap: Record<string, React.ReactNode> = {
                ScrollText: <ScrollText size={22} className="text-[#A8883C]" />,
                LineChart: <LineChart size={22} className="text-[#A8883C]" />,
                BookMarked: <BookMarked size={22} className="text-[#A8883C]" />,
                Globe: <Globe size={22} className="text-[#A8883C]" />,
                ShieldCheck: <ShieldCheck size={22} className="text-[#A8883C]" />,
                MessageSquareText: <MessageSquareText size={22} className="text-[#A8883C]" />,
              };

              return (
                <motion.div
                  key={feature.title}
                  variants={staggerItem}
                  className="card-premium p-8 md:p-10 h-full"
                  whileHover={{ y: -4, boxShadow: '0 8px 32px rgba(26,46,34,0.08)', borderColor: 'rgba(196,164,92,0.3)' }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mb-5">
                    {IconMap[feature.icon]}
                  </div>
                  <h3 className="font-serif text-lg font-normal italic text-brand-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="font-sans text-sm font-light text-beige-700 leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* ========== SAMPLE REPORT ========== */}
      <section className="dark-section py-28 md:py-36">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <ScrollReveal>
            <SectionHeading
              title="报告预览"
              subtitle="清晰的冲稳保方案，每个推荐都有数据支撑"
              light
            />
          </ScrollReveal>

          <ScrollReveal delay={0.2}>
            <div className="card-premium p-8 md:p-10 overflow-hidden">
              {/* Score */}
              <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8 pb-8 border-b border-[#E0D8CC]">
                <div className="text-center">
                  <div className="font-serif text-5xl font-light text-brand-900">582</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-1">总分</div>
                </div>
                <div className="w-px h-12 bg-[#E0D8CC] hidden md:block" />
                <div className="text-center">
                  <div className="font-mono text-2xl font-light text-brand-700">26,843</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-1">位次</div>
                </div>
                <div className="w-px h-12 bg-[#E0D8CC] hidden md:block" />
                <div className="text-center">
                  <div className="font-mono text-2xl font-light text-accent-gold">92%</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-500 mt-1">匹配度</div>
                </div>
              </div>

              {/* Tiers */}
              <motion.div
                className="grid grid-cols-1 md:grid-cols-3 gap-6"
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {/* 冲刺 */}
                <motion.div variants={staggerItem} className="p-6 rounded-xl bg-[#A84A3A]/5 border border-[#A84A3A]/10">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-[#A84A3A]" />
                    <span className="font-mono text-caption-mono text-[#A84A3A]">冲刺</span>
                    <span className="font-mono text-[10px] text-beige-500 ml-auto">30-50%</span>
                  </div>
                  <p className="font-sans text-sm font-light text-beige-700">浙江大学 · 计算机科学与技术</p>
                  <p className="font-sans text-xs font-light text-beige-500 mt-1">录取概率 35% · 预测位次 22,500</p>
                </motion.div>

                {/* 稳妥 */}
                <motion.div variants={staggerItem} className="p-6 rounded-xl bg-[#C4A45C]/5 border border-[#C4A45C]/10">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-[#C4A45C]" />
                    <span className="font-mono text-caption-mono text-[#C4A45C]">稳妥</span>
                    <span className="font-mono text-[10px] text-beige-500 ml-auto">50-80%</span>
                  </div>
                  <p className="font-sans text-sm font-light text-beige-700">武汉大学 · 软件工程</p>
                  <p className="font-sans text-xs font-light text-beige-500 mt-1">录取概率 68% · 预测位次 28,000</p>
                </motion.div>

                {/* 保底 */}
                <motion.div variants={staggerItem} className="p-6 rounded-xl bg-[#4A8A7A]/5 border border-[#4A8A7A]/10">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-[#4A8A7A]" />
                    <span className="font-mono text-caption-mono text-[#4A8A7A]">保底</span>
                    <span className="font-mono text-[10px] text-beige-500 ml-auto">&gt;80%</span>
                  </div>
                  <p className="font-sans text-sm font-light text-beige-700">华中科技大学 · 电子信息工程</p>
                  <p className="font-sans text-xs font-light text-beige-500 mt-1">录取概率 85% · 预测位次 32,000</p>
                </motion.div>
              </motion.div>

              {/* CTA */}
              <div className="text-center mt-8">
                <Button variant="gold" size="lg" href="/calculator">
                  生成你的专属方案
                </Button>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ========== PRICING ========== */}
      <section className="gold-section py-28 md:py-36">
        <div className="max-w-6xl mx-auto px-6 lg:px-8">
          <ScrollReveal>
            <SectionHeading
              title="价格方案"
              subtitle="选择适合你的方案，让志愿填报不再迷茫"
            />
          </ScrollReveal>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Free */}
            <ScrollReveal delay={0}>
              <motion.div
                className="card-premium p-8 md:p-10 text-center flex flex-col"
                whileHover={{ y: -4 }}
                transition={{ duration: 0.3 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mx-auto mb-5">
                  <Gem size={22} className="text-[#A8883C]" />
                </div>
                <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">免费版</h3>
                <p className="font-sans text-sm font-light text-beige-600 mb-6">快速了解志愿填报方向</p>
                <div className="flex items-baseline justify-center gap-3 mb-6">
                  <span className="font-serif text-4xl font-light text-brand-900">免费</span>
                </div>
                <ul className="space-y-3 mb-8 text-left flex-1">
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">AI 院校智能匹配（限5所）</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">基础录取机会评估</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">基础院校数据查询</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">志愿填报基础指南</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">志愿表预览（限10个志愿）</span>
                  </li>
                </ul>
                <Button variant="secondary" className="w-full" onClick={() => navigate('/calculator')}>
                  免费开始
                </Button>
              </motion.div>
            </ScrollReveal>

            {/* Basic - popular/recommended */}
            <ScrollReveal delay={0.08}>
              <motion.div
                className="relative card-premium p-8 md:p-10 text-center ring-2 ring-accent-gold shadow-[0_4px_20px_rgba(196,164,92,0.2)] flex flex-col"
                whileHover={{ y: -4 }}
                transition={{ duration: 0.3 }}
              >
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                  <motion.span
                    className="inline-block font-mono text-[10px] uppercase tracking-[0.2em] bg-accent-gold text-brand-900 px-4 py-1 rounded-full"
                    animate={{ boxShadow: ['0 0 0 0 rgba(196,164,92,0.4)', '0 0 0 8px rgba(196,164,92,0)', '0 0 0 0 rgba(196,164,92,0)'] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    推荐
                  </motion.span>
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mx-auto mb-5 mt-1">
                  <Sparkles size={22} className="text-[#A8883C]" />
                </div>
                <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">基础版</h3>
                <p className="font-sans text-sm font-light text-beige-600 mb-6">生成一份完整可用的志愿方案</p>
                <div className="flex items-baseline justify-center gap-3 mb-1">
                  <span className="font-serif text-4xl font-light text-brand-900">¥49</span>
                  <span className="font-mono text-sm text-beige-500 line-through">¥99</span>
                </div>
                <span className="font-serif text-xs italic text-accent-gold block mb-6">限时优惠</span>
                <ul className="space-y-3 mb-8 text-left flex-1">
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">AI 院校智能匹配（不限量）</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">录取机会评估</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">冲稳保策略分析</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">完整志愿表生成</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">基础个性化分析报告</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">365 天有效</span>
                  </li>
                </ul>
                <Button variant="gold" className="w-full" onClick={() => navigate('/checkout?plan=basic')}>
                  选择基础版 - 限时优惠
                </Button>
              </motion.div>
            </ScrollReveal>

            {/* Advanced */}
            <ScrollReveal delay={0.16}>
              <motion.div
                className="card-premium p-8 md:p-10 text-center flex flex-col"
                whileHover={{ y: -4 }}
                transition={{ duration: 0.3 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mx-auto mb-5">
                  <Star size={22} className="text-[#A8883C]" />
                </div>
                <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">进阶版</h3>
                <p className="font-sans text-sm font-light text-beige-600 mb-6">看清专业组与调剂风险</p>
                <div className="flex items-baseline justify-center gap-3 mb-1">
                  <span className="font-serif text-4xl font-light text-brand-900">¥129</span>
                  <span className="font-mono text-sm text-beige-500 line-through">¥199</span>
                </div>
                <span className="font-serif text-xs italic text-accent-gold block mb-6">限时优惠</span>
                <ul className="space-y-3 mb-8 text-left flex-1">
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">全部基础版功能</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">专业倾向测评</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">位次风险深度分析</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">专业就业前景解读</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">AI 深度答疑</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">365 天有效</span>
                  </li>
                </ul>
                <Button variant="primary" className="w-full" onClick={() => navigate('/checkout?plan=advanced')}>
                  选择进阶版
                </Button>
              </motion.div>
            </ScrollReveal>

            {/* Premium */}
            <ScrollReveal delay={0.24}>
              <motion.div
                className="card-premium p-8 md:p-10 text-center flex flex-col"
                whileHover={{ y: -4 }}
                transition={{ duration: 0.3 }}
              >
                <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mx-auto mb-5">
                  <Award size={22} className="text-[#A8883C]" />
                </div>
                <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">尊享版</h3>
                <p className="font-sans text-sm font-light text-beige-600 mb-6">人工复核你的最终志愿方案</p>
                <div className="flex items-baseline justify-center gap-3 mb-1">
                  <span className="font-serif text-4xl font-light text-brand-900">¥399</span>
                  <span className="font-mono text-sm text-beige-500 line-through">¥599</span>
                </div>
                <span className="font-serif text-xs italic text-accent-gold block mb-6">限时优惠</span>
                <ul className="space-y-3 mb-8 text-left flex-1">
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">全部进阶版功能</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">人工志愿方案复核 1 次</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">志愿方案深度优化</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">录取结果跟踪提醒</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">大学入学建议</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                    <span className="font-sans text-sm font-light text-[#4A4A4A]">365 天有效</span>
                  </li>
                </ul>
                <Button variant="primary" className="w-full" onClick={() => navigate('/checkout?plan=premium')}>
                  选择尊享版
                </Button>
              </motion.div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* ========== FAQ ========== */}
      <section id="faq" className="bg-white py-28 md:py-36">
        <div className="max-w-3xl mx-auto px-6 lg:px-8">
          <ScrollReveal>
            <SectionHeading
              title="常见问题"
              subtitle="关于择境 ZENPATH 你可能想了解的问题"
            />
          </ScrollReveal>

          <ScrollReveal delay={0.15}>
            <div className="card-premium overflow-hidden">
              {FAQS.map((faq) => (
                <FAQItem
                  key={faq.id}
                  faq={faq}
                  isOpen={openFaq === faq.id}
                  onClick={() => toggleFaq(faq.id)}
                />
              ))}
            </div>
          </ScrollReveal>
        </div>
      </section>

      {/* ========== CTA SECTION ========== */}
      <section className="dark-section py-28 md:py-36 overflow-hidden">
        {/* Subtle moving pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'radial-gradient(circle at 30% 40%, rgba(196,164,92,0.3) 0%, transparent 50%), radial-gradient(circle at 70% 60%, rgba(255,255,255,0.1) 0%, transparent 50%)',
            animation: 'kenBurns 25s ease-in-out infinite alternate',
          }}
        />

        <div className="max-w-4xl mx-auto px-6 lg:px-8 text-center relative z-10">
          <motion.h2
            className="font-serif text-h2 text-accent-gold mb-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            立即开始你的志愿规划
          </motion.h2>
          <motion.p
            className="font-sans text-lg font-light italic text-white/60 max-w-2xl mx-auto mb-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15, duration: 0.7 }}
          >
            注册即享免费评估，AI 为你生成科学可依的专属志愿方案
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.7 }}
          >
            <Button variant="gold" size="lg" href="/calculator">
              免费开始评估
            </Button>
          </motion.div>
        </div>
      </section>
    </>
  );
}
