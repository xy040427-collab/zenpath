import { motion } from 'framer-motion';

interface LoadingSkeletonProps {
  type?: 'card' | 'text' | 'chart' | 'table';
  count?: number;
}

function ShimmerBlock({ className = '', delay = 0 }: { className?: string; delay?: number }) {
  return (
    <motion.div
      className={`rounded bg-gradient-to-r from-beige-100 via-beige-50 to-beige-100 bg-[length:200%_100%] ${className}`}
      initial={{ backgroundPosition: '200% 0' }}
      animate={{ backgroundPosition: '-200% 0' }}
      transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut', delay }}
    />
  );
}

export default function LoadingSkeleton({ type = 'card', count = 9 }: LoadingSkeletonProps) {
  if (type === 'card') {
    return (
      <div className="space-y-6">
        {/* Tab bar skeleton */}
        <div className="flex gap-3 justify-center">
          {['冲', '稳', '保', '垫'].map((label, i) => (
            <ShimmerBlock
              key={label}
              delay={i * 0.08}
              className="w-20 h-9 rounded-full"
            />
          ))}
        </div>

        {/* Summary line */}
        <div className="flex justify-center">
          <ShimmerBlock delay={0.3} className="w-64 h-3" />
        </div>

        {/* Card grid — matches actual 3-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 max-w-[1600px] mx-auto">
          {Array.from({ length: count }).map((_, i) => (
            <motion.div
              key={i}
              className="card-premium p-4 h-72 flex flex-col"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.3 }}
            >
              {/* Header: badge + title + score */}
              <div className="flex items-start gap-2.5">
                <ShimmerBlock delay={i * 0.05} className="w-9 h-9 rounded-full shrink-0" />
                <div className="flex-1 space-y-1">
                  <ShimmerBlock delay={i * 0.06} className="h-4 w-3/4" />
                  <ShimmerBlock delay={i * 0.07} className="h-2.5 w-1/2" />
                </div>
                <div className="text-right shrink-0 space-y-0.5">
                  <ShimmerBlock delay={i * 0.06} className="h-5 w-12 ml-auto" />
                  <ShimmerBlock delay={i * 0.07} className="h-2 w-14 ml-auto" />
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-4 gap-1.5 mt-2.5">
                {Array.from({ length: 4 }).map((_, j) => (
                  <div key={j} className="text-center p-1 rounded bg-beige-50/50">
                    <ShimmerBlock delay={i * 0.08 + j * 0.02} className="h-3 w-3/4 mx-auto" />
                    <ShimmerBlock delay={i * 0.09 + j * 0.02} className="h-2 w-1/2 mx-auto mt-0.5" />
                  </div>
                ))}
              </div>

              {/* Major tags preview */}
              <div className="mt-2.5 space-y-1.5">
                <ShimmerBlock delay={i * 0.1} className="h-2 w-16" />
                <div className="flex flex-wrap gap-0.5">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <ShimmerBlock key={j} delay={i * 0.1 + j * 0.02} className="h-4 w-16 rounded" />
                  ))}
                </div>
              </div>

              {/* Reason lines */}
              <div className="mt-2 space-y-1">
                <ShimmerBlock delay={i * 0.12} className="h-2.5 w-full" />
                <ShimmerBlock delay={i * 0.13} className="h-2.5 w-5/6" />
              </div>

              {/* Tags */}
              <div className="flex gap-1 mt-auto pt-1">
                <ShimmerBlock delay={i * 0.14} className="h-3 w-12 rounded" />
                <ShimmerBlock delay={i * 0.15} className="h-3 w-10 rounded" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div className="card-premium p-8 space-y-4">
        <ShimmerBlock className="h-5 w-1/3" />
        <ShimmerBlock className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div className="space-y-3">
        <div className="flex gap-4 pb-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <ShimmerBlock key={i} delay={i * 0.05} className="h-3 w-1/5" />
          ))}
        </div>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: 5 }).map((_, j) => (
              <ShimmerBlock key={j} delay={i * 0.04 + j * 0.03} className="h-7 w-1/5 rounded" />
            ))}
          </div>
        ))}
      </div>
    );
  }

  // Text type
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <ShimmerBlock key={i} delay={i * 0.06} className={`h-4 rounded ${i === count - 1 ? 'w-2/3' : 'w-full'}`} />
      ))}
    </div>
  );
}
