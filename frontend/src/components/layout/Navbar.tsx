import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { NAV_LINKS, BRAND } from '../../utils/constants';
import Button from '../common/Button';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';
  const isChat = location.pathname === '/chat';

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setIsMobileOpen(false);
  }, [location]);

  // Dark mode on home page (unscrolled) OR any page with dark hero (university detail, etc.)
  const isDark = (isHome && !isScrolled) || (!isScrolled && location.pathname.startsWith('/university/'));

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isChat
          ? 'bg-white/95 backdrop-blur-xl border-b border-[#E0D8CC]'
          : isScrolled
          ? 'bg-white/80 backdrop-blur-xl border-b border-[#E0D8CC]/30 shadow-[0_1px_8px_rgba(26,46,34,0.04)]'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <motion.div
              className="w-9 h-9 rounded-full overflow-hidden flex items-center justify-center transition-all duration-500"
              animate={{ y: [0, -2, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            >
              <img src="/favicon.png" alt="择境" className="w-full h-full object-cover" />
            </motion.div>
            <div className="flex items-baseline gap-2.5">
              <span
                className={`font-serif text-lg font-light tracking-wider transition-colors duration-500 ${
                  isDark ? 'text-white' : 'text-brand-900'
                }`}
              >
                {BRAND.name}
              </span>
              <span
                className={`font-mono text-[10px] uppercase tracking-[0.25em] transition-colors duration-500 ${
                  isDark ? 'text-white/40' : 'text-beige-500'
                }`}
              >
                ZENPATH
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => {
              const isActive = location.pathname === link.href;
              return (
                <Link
                  key={link.href}
                  to={link.href}
                  className={`relative text-sm font-medium tracking-wide transition-colors duration-300 group ${
                    isActive
                      ? isDark
                        ? 'text-white'
                        : 'text-brand-700'
                      : isDark
                      ? 'text-white/60 hover:text-white/90'
                      : 'text-beige-600 hover:text-brand-700'
                  }`}
                >
                  {link.label}
                  {/* Underline animation on hover */}
                  <span className={`absolute -bottom-1 left-0 h-[2px] bg-current transition-all duration-300 rounded-full ${
                    isActive ? 'w-full' : 'w-0 group-hover:w-full'
                  }`} />
                  {/* Active dot indicator */}
                  {isActive && (
                    <motion.span
                      className="absolute -bottom-[5px] left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-accent-gold"
                      layoutId="activeDot"
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
            <Button
              variant={isDark ? 'gold' : 'primary'}
              size="sm"
              href="/calculator"
              className="ml-2 animate-pulse-gold"
            >
              开始评估
            </Button>
          </div>

          {/* Mobile Toggle */}
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            className={`md:hidden p-2 rounded-lg transition-colors ${
              isDark ? 'text-white/70 hover:bg-white/10' : 'text-brand-900 hover:bg-beige-200'
            }`}
            aria-label="Toggle menu"
          >
            {isMobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu - Slide-in drawer from right */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            className="fixed inset-0 top-20 z-40 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Backdrop */}
            <motion.div
              className="absolute inset-0 bg-brand-900/20 backdrop-blur-sm"
              onClick={() => setIsMobileOpen(false)}
            />
            {/* Drawer */}
            <motion.div
              className="absolute right-0 top-0 bottom-0 w-72 bg-white/95 backdrop-blur-xl border-l border-beige-200 shadow-2xl"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            >
              <div className="p-6 space-y-3">
                {NAV_LINKS.map((link) => {
                  const isActive = location.pathname === link.href;
                  return (
                    <Link
                      key={link.href}
                      to={link.href}
                      className={`block text-sm font-medium tracking-wide py-3 px-4 rounded-xl transition-colors ${
                        isActive
                          ? 'text-brand-700 bg-brand-50'
                          : 'text-beige-600 hover:text-brand-700 hover:bg-beige-100'
                      }`}
                    >
                      {link.label}
                    </Link>
                  );
                })}
                <div className="pt-4 px-1">
                  <Button
                    variant="primary"
                    size="md"
                    className="w-full"
                    href="/calculator"
                  >
                    开始评估
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
