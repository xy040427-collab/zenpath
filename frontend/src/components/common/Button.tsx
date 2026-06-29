import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import type { ReactNode } from 'react';

const MotionLink = motion(Link);

interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'gold' | 'premium';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  href,
  onClick,
  disabled = false,
  loading = false,
  type = 'button',
}: ButtonProps) {
  const baseClasses =
    'inline-flex items-center justify-center font-mono uppercase tracking-[0.15em] rounded-btn transition-all duration-300';

  const sizeClasses = {
    sm: 'text-[10px] px-3 py-1.5',
    md: 'text-btn px-5 py-2.5',
    lg: 'text-btn px-8 py-3.5',
  };

  const variantClasses = {
    primary:
      'bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed',
    secondary:
      'bg-beige-200 text-brand-900 hover:bg-beige-300 disabled:opacity-50 disabled:cursor-not-allowed',
    outline:
      'border border-white/30 text-white/90 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed',
    ghost:
      'text-beige-600 hover:text-brand-900 hover:bg-beige-200 disabled:opacity-50 disabled:cursor-not-allowed',
    gold:
      'bg-accent-gold text-brand-900 hover:bg-accent-gold-dark disabled:opacity-50 disabled:cursor-not-allowed',
    premium:
      'bg-brand-700 text-accent-gold border border-accent-gold/30 hover:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed',
  };

  const content = loading ? (
    <span className="flex items-center gap-2">
      <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
      加载中...
    </span>
  ) : (
    children
  );

  const motionProps = {
    whileHover: disabled ? {} : { y: -1 },
    whileTap: disabled ? {} : { scale: 0.97 },
    transition: { duration: 0.2 },
  };

  if (href) {
    if (href.startsWith('#')) {
      return (
        <motion.a
          href={href}
          className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
          {...motionProps}
        >
          {content}
        </motion.a>
      );
    }
    return (
      <MotionLink
        to={href}
        className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
        {...motionProps}
      >
        {content}
      </MotionLink>
    );
  }

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`}
      {...motionProps}
    >
      {content}
    </motion.button>
  );
}
