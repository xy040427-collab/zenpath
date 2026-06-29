import { motion } from 'framer-motion';
import { CircleCheckBig, Gem, Sparkles, Crown, Medal } from 'lucide-react';
import type { PricingTier } from '../../types';
import { formatPrice } from '../../utils/formatters';
import Button from './Button';

interface PricingCardProps {
  tier: PricingTier;
  index?: number;
  onSelect?: (tier: PricingTier) => void;
}

const icons: Record<string, typeof Gem> = {
  free: Gem,
  basic: Sparkles,
  advanced: Crown,
  premium: Medal,
  ultimate: Medal,
};

export default function PricingCard({ tier, index = 0, onSelect }: PricingCardProps) {
  const Icon = icons[tier.id] || Gem;

  return (
    <motion.div
      className={`relative card-premium p-8 md:p-10 flex flex-col ${
        tier.isPopular ? 'ring-2 ring-accent-gold shadow-gold' : ''
      }`}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay: index * 0.12 }}
      whileHover={{ y: -4 }}
    >
      {/* Popular badge */}
      {tier.isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-block font-mono text-[10px] uppercase tracking-[0.2em] bg-accent-gold text-brand-900 px-4 py-1 rounded-full">
            {tier.badge}
          </span>
        </div>
      )}

      {/* Icon */}
      <div className="w-12 h-12 rounded-xl bg-accent-gold-light flex items-center justify-center mb-6">
        <Icon size={22} className="text-accent-gold-dark" />
      </div>

      {/* Name & Description */}
      <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">{tier.name}</h3>
      <p className="font-sans text-sm font-light text-beige-600 mb-6">{tier.description}</p>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-3">
          <span className="font-serif text-4xl font-light text-brand-900">
            {tier.price === 0 ? '免费' : formatPrice(tier.price)}
          </span>
          {tier.originalPrice && (
            <span className="font-mono text-sm text-beige-500 line-through">
              {formatPrice(tier.originalPrice)}
            </span>
          )}
        </div>
        {tier.badge && tier.id !== 'free' && (
          <span className="font-serif text-xs italic text-accent-gold mt-1 block">
            {tier.originalPrice ? '限时优惠' : '限时优惠'}
          </span>
        )}
      </div>

      {/* Features */}
      <ul className="flex-1 space-y-3 mb-8">
        {tier.features.map((feature, fi) => (
          <li key={fi} className="flex items-start gap-3">
            <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
            <span className="font-sans text-sm font-light text-ink leading-relaxed">{feature}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <Button
        variant={tier.isPopular ? 'gold' : tier.id === 'free' ? 'outline' : 'primary'}
        className="w-full"
        onClick={() => onSelect?.(tier)}
      >
        {tier.id === 'free' ? '免费开始' : `选择${tier.name}`}
      </Button>
    </motion.div>
  );
}
