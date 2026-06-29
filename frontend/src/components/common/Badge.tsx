import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'gold' | 'ruby' | 'teal' | 'outline';
  size?: 'sm' | 'md';
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className = '',
}: BadgeProps) {
  const baseClasses = 'inline-flex items-center gap-1.5 font-mono uppercase tracking-[0.2em] rounded-full';

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-[11px] px-3 py-1',
  };

  const variantClasses = {
    default: 'bg-brand-100 text-brand-700',
    gold: 'bg-[#B8962E]/10 text-[#B8962E] border border-[#B8962E]/20',
    ruby: 'bg-[#9B1D3F]/10 text-[#9B1D3F] border border-[#9B1D3F]/20',
    teal: 'bg-[#2D7D6A]/10 text-[#2D7D6A] border border-[#2D7D6A]/20',
    outline: 'bg-transparent text-beige-600 border border-beige-300',
  };

  return (
    <motion.span
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25 }}
    >
      {children}
    </motion.span>
  );
}
