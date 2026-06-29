import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Star, Sprout, Gem, CircleCheckBig } from 'lucide-react';
import { PRICING_TIERS } from '../utils/constants';
import { formatPrice } from '../utils/formatters';
import Button from '../components/common/Button';

const tierIcons = [Gem, Sparkles, Star, Sprout];

const staggerContainer = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
};

const staggerItem = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

export default function Pricing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="font-serif text-h2 text-brand-900 mb-3">价格方案</h1>
          <p className="font-sans text-lg font-light italic text-beige-600 max-w-xl mx-auto">
            选择适合你的方案，开启科学志愿填报之旅
          </p>
        </motion.div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          {PRICING_TIERS.map((tier, i) => {
            const Icon = tierIcons[i];
            return (
              <motion.div
                key={tier.id}
                className={`relative card-premium p-8 md:p-10 flex flex-col ${
                  tier.isPopular ? 'ring-2 ring-accent-gold shadow-[0_4px_20px_rgba(196,164,92,0.2)]' : ''
                }`}
                variants={staggerItem}
                whileHover={{ y: -4, boxShadow: '0 8px 32px rgba(26,46,34,0.08)' }}
                transition={{ duration: 0.3 }}
              >
                {tier.isPopular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                    <motion.span
                      className="inline-block font-mono text-[10px] uppercase tracking-[0.2em] bg-accent-gold text-brand-900 px-4 py-1 rounded-full"
                      animate={{ boxShadow: ['0 0 0 0 rgba(196,164,92,0.4)', '0 0 0 8px rgba(196,164,92,0)', '0 0 0 0 rgba(196,164,92,0)'] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      {tier.badge}
                    </motion.span>
                  </div>
                )}

                <div className="w-12 h-12 rounded-xl bg-[#E8DCC0] flex items-center justify-center mb-6">
                  <Icon size={22} className="text-[#A8883C]" />
                </div>

                <h3 className="font-serif text-2xl font-normal text-brand-900 mb-2">{tier.name}</h3>
                <p className="font-sans text-sm font-light text-beige-600 mb-6">{tier.description}</p>

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
                  {tier.originalPrice && (
                    <span className="font-serif text-xs italic text-accent-gold mt-1 block">
                      限时优惠
                    </span>
                  )}
                </div>

                <ul className="flex-1 space-y-3 mb-8">
                  {tier.features.map((feature, fi) => (
                    <li key={fi} className="flex items-start gap-3">
                      <CircleCheckBig size={15} className="text-accent-gold mt-0.5 shrink-0" />
                      <span className="font-sans text-sm font-light text-[#4A4A4A] leading-relaxed">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  variant={tier.isPopular ? 'gold' : tier.id === 'free' ? 'secondary' : 'primary'}
                  className="w-full"
                  onClick={() => {
                    if (tier.id === 'free') {
                      navigate('/calculator');
                    } else {
                      navigate(`/checkout?plan=${tier.id}`);
                    }
                  }}
                >
                  {tier.id === 'free' ? '免费开始' : `选择${tier.name}`}
                </Button>
              </motion.div>
            );
          })}
        </motion.div>

        {/* FAQ teaser */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          <p className="font-sans text-sm font-light text-beige-600 mb-4">
            有任何疑问？查看我们的
          </p>
          <Button variant="ghost" size="sm" href="/#faq">
            常见问题
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
