import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  text?: string;
  size?: number;
}

export default function LoadingSpinner({ text = '加载中...', size = 48 }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <motion.div
        className="rounded-full border-2 border-beige-200 border-t-brand-900"
        style={{ width: size, height: size }}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
      {text && (
        <p className="font-sans text-sm font-light text-beige-600 tracking-wide">
          {text}
        </p>
      )}
    </div>
  );
}
