import { motion, AnimatePresence } from 'framer-motion';
import { CircleCheckBig, AlertCircle, Info, X } from 'lucide-react';
import type { ToastMessage } from '../../types';

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

const icons = {
  success: CircleCheckBig,
  error: AlertCircle,
  warning: AlertCircle,
  info: Info,
};

const colors = {
  success: 'bg-accent-teal/10 text-accent-teal border-accent-teal/20',
  error: 'bg-accent-ruby/10 text-accent-ruby border-accent-ruby/20',
  warning: 'bg-accent-gold-light text-accent-gold-dark border-accent-gold/20',
  info: 'bg-brand-100 text-brand-700 border-brand-200',
};

export default function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div className="fixed top-6 right-6 z-[10000] flex flex-col gap-3 max-w-sm">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              className={`flex items-start gap-3 px-5 py-4 rounded-xl border ${colors[toast.type]} backdrop-blur-md`}
              initial={{ opacity: 0, x: 100, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.95 }}
              layout
              transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <p className="flex-1 font-sans text-sm font-light leading-relaxed">{toast.message}</p>
              <button
                onClick={() => onDismiss(toast.id)}
                className="shrink-0 p-0.5 rounded hover:bg-black/5 transition-colors"
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
