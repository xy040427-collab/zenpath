import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface GaugeChartProps {
  value: number;
  maxValue?: number;
  label?: string;
  sublabel?: string;
  size?: number;
  color?: string;
}

export default function GaugeChart({
  value,
  maxValue = 100,
  label,
  sublabel,
  size = 200,
  color = '#2D4A3E',
}: GaugeChartProps) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      let frame: number;
      const startTime = performance.now();
      const duration = 1500;
      const target = Math.min(value / maxValue, 1);
      const animate = (now: number) => {
        const elapsed = (now - startTime) / 1000;
        const progress = Math.min(elapsed / (duration / 1000), 1);
        const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        setAnimatedValue(eased * target);
        if (progress < 1) frame = requestAnimationFrame(animate);
      };
      frame = requestAnimationFrame(animate);
      return () => cancelAnimationFrame(frame);
    }, 300);
    return () => clearTimeout(timer);
  }, [value, maxValue]);

  const percentage = Math.min(value / maxValue, 1);
  const angle = animatedValue * 180;
  const radius = 80;
  const strokeWidth = 12;
  const cx = size / 2;
  const cy = size / 2 + 10;
  const normalizedRadius = radius - strokeWidth / 2;
  const startAngle = 180;
  const endAngle = startAngle + angle;

  const polarToCartesian = (cx: number, cy: number, r: number, angleDeg: number) => {
    const angleRad = ((angleDeg - 180) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(angleRad),
      y: cy + r * Math.sin(angleRad),
    };
  };

  const start = polarToCartesian(cx, cy, normalizedRadius, startAngle);
  const end = polarToCartesian(cx, cy, normalizedRadius, endAngle);

  const largeArcFlag = angle > 180 ? 1 : 0;
  const d = `M ${start.x} ${start.y} A ${normalizedRadius} ${normalizedRadius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;

  const bgStart = polarToCartesian(cx, cy, normalizedRadius, startAngle);
  const bgEnd = polarToCartesian(cx, cy, normalizedRadius, 360);
  const bgLargeArc = 180 > 180 ? 1 : 0;
  const bgD = `M ${bgStart.x} ${bgStart.y} A ${normalizedRadius} ${normalizedRadius} 0 ${bgLargeArc} 1 ${bgEnd.x} ${bgEnd.y}`;

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size / 2 + 30} viewBox={`0 0 ${size} ${size / 2 + 30}`}>
        {/* Background arc */}
        <path d={bgD} fill="none" stroke="#EDE6D8" strokeWidth={strokeWidth} strokeLinecap="round" />
        {/* Value arc with sweep animation */}
        <motion.path
          d={d}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, ease: [0.25, 0.46, 0.45, 0.94] }}
        />
        {/* Needle */}
        {endAngle > 180 && (
          <motion.line
            x1={cx}
            y1={cy}
            x2={end.x}
            y2={end.y}
            stroke={color}
            strokeWidth={2.5}
            strokeLinecap="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.3 }}
          />
        )}
      </svg>
      <motion.div
        className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.5 }}
      >
        <div className="font-serif text-3xl font-light text-brand-900">
          {Math.round(animatedValue * 100)}%
        </div>
        {label && (
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-beige-600 mt-1">
            {label}
          </div>
        )}
      </motion.div>
      {sublabel && (
        <div className="font-sans text-xs font-light text-beige-600 mt-2">{sublabel}</div>
      )}
    </div>
  );
}
