import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShieldCheck, ChevronRight, ArrowLeft, CircleCheckBig, AlertCircle, CreditCard, Smartphone } from 'lucide-react';
import { PRICING_TIERS } from '../utils/constants';
import { formatPrice } from '../utils/formatters';
import Button from '../components/common/Button';

interface OrderData {
  order_id: string;
  order_no: string;
  plan_code: string;
  original_amount: number;
  discount_amount: number;
  pay_amount: number;
  status: string;
}

export default function Checkout() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const planId = searchParams.get('plan') || 'advanced';
  const [couponCode, setCouponCode] = useState('');
  const [couponApplied, setCouponApplied] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'wechat' | 'alipay'>('wechat');
  const [orderData, setOrderData] = useState<OrderData | null>(null);
  const [loading, setLoading] = useState(false);
  const [paid, setPaid] = useState(false);

  const tier = PRICING_TIERS.find((t) => t.id === planId) || PRICING_TIERS[1];
  if (!tier) return null;

  const handleCreateOrder = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          application_id: 'app_mock',
          plan_code: planId,
          coupon_code: couponApplied ? couponCode : undefined,
        }),
      });
      const data = await resp.json();
      if (data.success) {
        setOrderData(data.data);
      }
    } catch {
      setOrderData({
        order_id: `order_${Date.now()}`,
        order_no: `GKV${Date.now()}`,
        plan_code: planId,
        original_amount: tier.price,
        discount_amount: couponApplied ? Math.round(tier.price * 0.15) : 0,
        pay_amount: couponApplied ? Math.round(tier.price * 0.85) : tier.price,
        status: 'pending',
      });
    }
    setLoading(false);
  };

  const handlePay = async () => {
    if (!orderData) return;
    setLoading(true);
    try {
      const resp = await fetch(`/api/v1/orders/${orderData.order_id}/pay`, {
        method: 'POST',
      });
      const data = await resp.json();
      if (data.success) {
        setPaid(true);
      }
    } catch {
      setPaid(true);
    }
    setLoading(false);
  };

  const applyCoupon = () => {
    if (couponCode.trim().toUpperCase() === 'GAOKAO2026') {
      setCouponApplied(true);
    }
  };

  if (paid) {
    return (
      <div className="min-h-screen pt-28 md:pt-32 pb-20 bg-[#F5F0E8] flex items-center justify-center">
        <motion.div
          className="max-w-md mx-auto px-6 text-center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="w-20 h-20 rounded-full bg-brand-50 flex items-center justify-center mx-auto mb-6"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.15 }}
          >
            <CircleCheckBig size={40} className="text-accent-gold" />
          </motion.div>
          <h1 className="font-serif text-h2 text-brand-900 mb-3">支付成功！</h1>
          <p className="font-sans text-base font-light text-beige-600 mb-8">
            你的 <strong className="text-brand-700">{tier.name}</strong> 订单已完成支付，现在可以查看完整报告了。
          </p>
          <div className="space-y-3">
            <Button variant="gold" className="w-full" onClick={() => navigate('/report')}>
              查看我的报告
            </Button>
            <Button variant="outline" className="w-full" onClick={() => navigate('/')}>
              返回首页
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-28 md:pt-32 pb-20">
      <div className="max-w-4xl mx-auto px-6 lg:px-8">
        {/* Back */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Link
            to="/pricing"
            className="inline-flex items-center gap-2 font-sans text-sm text-beige-600 hover:text-brand-700 transition-colors mb-10 group"
          >
            <motion.span className="group-hover:-translate-x-1 transition-transform duration-200 inline-block">
              <ArrowLeft size={14} />
            </motion.span>
            返回价格方案
          </Link>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
          {/* Left — Order Form */}
          <div className="lg:col-span-3">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="font-serif text-h2 text-brand-900 mb-2">确认订单</h1>
              <p className="font-sans text-base font-light text-beige-600 mb-8">请确认你的订单信息并选择支付方式</p>

              {/* Selected Plan Summary */}
              <div className="card-premium p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="font-mono text-caption-mono text-beige-500 mb-1 block">已选方案</span>
                    <h3 className="font-serif text-xl text-brand-900">{tier.name}</h3>
                  </div>
                  <motion.span
                    className="font-serif text-2xl text-brand-900"
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
                  >
                    {formatPrice(tier.price)}
                  </motion.span>
                </div>
                {tier.isPopular && (
                  <span className="inline-block font-mono text-[10px] uppercase tracking-[0.2em] bg-accent-gold/20 text-[#A8883C] px-3 py-1 rounded-full mb-3">
                    推荐
                  </span>
                )}
                <ul className="space-y-2">
                  {tier.features.slice(0, 4).map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CircleCheckBig size={13} className="text-accent-gold mt-1 shrink-0" />
                      <span className="font-sans text-sm text-[#4A4A4A]">{f}</span>
                    </li>
                  ))}
                  {tier.features.length > 4 && (
                    <li className="font-sans text-xs text-beige-500 italic">+{tier.features.length - 4} 项更多权益</li>
                  )}
                </ul>
              </div>

              {/* Coupon */}
              <div className="card-premium p-6 mb-6">
                <h4 className="font-sans text-sm font-medium text-brand-700 mb-3 flex items-center gap-2">
                  <AlertCircle size={14} />
                  优惠码
                </h4>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value)}
                    placeholder="输入优惠码"
                    className="flex-1 px-4 py-2.5 rounded-lg border border-[#E0D8CC] bg-white font-sans text-sm text-[#4A4A4A] outline-none focus:border-accent-gold transition-colors"
                    disabled={couponApplied}
                  />
                  <button
                    onClick={applyCoupon}
                    disabled={couponApplied || !couponCode.trim()}
                    className="px-5 py-2.5 rounded-lg bg-brand-700 text-white text-sm font-medium hover:bg-brand-800 disabled:opacity-40 transition-all"
                  >
                    {couponApplied ? '已使用' : '使用'}
                  </button>
                </div>
                {couponApplied && (
                  <motion.p
                    className="font-sans text-xs text-accent-gold mt-2"
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    ✅ 优惠码已使用，享受 15% 折扣
                  </motion.p>
                )}
                <p className="font-sans text-[11px] text-beige-500 mt-2">提示：输入 GAOKAO2026 享受限时优惠</p>
              </div>

              {/* Payment Method */}
              <div className="card-premium p-6 mb-6">
                <h4 className="font-sans text-sm font-medium text-brand-700 mb-4 flex items-center gap-2">
                  <CreditCard size={14} />
                  选择支付方式
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <motion.button
                    onClick={() => setPaymentMethod('wechat')}
                    className={`flex items-center justify-center gap-3 p-4 rounded-xl border-2 transition-all ${
                      paymentMethod === 'wechat'
                        ? 'border-accent-gold bg-accent-gold/5'
                        : 'border-[#E0D8CC] bg-white hover:border-beige-400'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Smartphone size={18} className={paymentMethod === 'wechat' ? 'text-[#A8883C]' : 'text-beige-500'} />
                    <span className={`font-sans text-sm font-medium ${paymentMethod === 'wechat' ? 'text-brand-700' : 'text-[#4A4A4A]'}`}>
                      微信支付
                    </span>
                  </motion.button>
                  <motion.button
                    onClick={() => setPaymentMethod('alipay')}
                    className={`flex items-center justify-center gap-3 p-4 rounded-xl border-2 transition-all ${
                      paymentMethod === 'alipay'
                        ? 'border-accent-gold bg-accent-gold/5'
                        : 'border-[#E0D8CC] bg-white hover:border-beige-400'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Smartphone size={18} className={paymentMethod === 'alipay' ? 'text-[#A8883C]' : 'text-beige-500'} />
                    <span className={`font-sans text-sm font-medium ${paymentMethod === 'alipay' ? 'text-brand-700' : 'text-[#4A4A4A]'}`}>
                      支付宝
                    </span>
                  </motion.button>
                </div>
              </div>

              {/* Action */}
              <motion.button
                onClick={orderData ? handlePay : handleCreateOrder}
                disabled={loading}
                className="w-full py-3.5 rounded-lg bg-accent-gold text-brand-900 font-mono text-btn uppercase tracking-[0.15em] font-medium hover:bg-[#A8883C] hover:text-white transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
              >
                {loading ? '处理中...' : orderData ? `确认支付 ${formatPrice(orderData.pay_amount)}` : `立即下单 ${formatPrice(tier.price)}`}
                {!loading && <ChevronRight size={14} />}
              </motion.button>

              <p className="font-sans text-[11px] text-beige-500 text-center mt-4 flex items-center justify-center gap-1.5">
                <ShieldCheck size={12} />
                支付安全由 SSL 加密保障
              </p>
            </motion.div>
          </div>

          {/* Right — Order Summary */}
          <div className="lg:col-span-2">
            <motion.div
              className="card-premium p-6 sticky top-28"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15 }}
            >
              <h4 className="font-mono text-caption-mono text-beige-500 mb-4">订单摘要</h4>
              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="font-sans text-sm text-[#4A4A4A]">{tier.name}</span>
                  <span className="font-sans text-sm text-brand-900">{formatPrice(tier.price)}</span>
                </div>
                {couponApplied && (
                  <motion.div
                    className="flex justify-between"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <span className="font-sans text-sm text-accent-gold">折扣 (15%)</span>
                    <span className="font-sans text-sm text-accent-gold">-{formatPrice(Math.round(tier.price * 0.15))}</span>
                  </motion.div>
                )}
                <div className="border-t border-[#E0D8CC] pt-3 flex justify-between">
                  <span className="font-sans text-sm font-medium text-brand-900">合计</span>
                  <span className="font-serif text-xl text-brand-900">
                    {couponApplied ? formatPrice(Math.round(tier.price * 0.85)) : formatPrice(tier.price)}
                  </span>
                </div>
              </div>

              {orderData && (
                <div className="text-center">
                  <p className="font-mono text-[10px] text-beige-500">订单号</p>
                  <p className="font-mono text-xs text-brand-700">{orderData.order_no}</p>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-[#E0D8CC]">
                <p className="font-sans text-[11px] text-beige-600 leading-relaxed">
                  支付即表示你同意 <Link to="/terms" className="text-[#A8883C] underline">服务条款</Link> 和 <Link to="/privacy" className="text-[#A8883C] underline">隐私政策</Link>。
                  本报告仅供参考，不保证录取结果。
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
