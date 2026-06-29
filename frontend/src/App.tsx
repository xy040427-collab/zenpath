import { useState, useCallback } from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import MainLayout from './components/layout/MainLayout';
import ToastContainer from './components/common/Toast';
import Home from './pages/Home';
import Calculator from './pages/Calculator';
import Preview from './pages/Preview';
import Pricing from './pages/Pricing';
import Checkout from './pages/Checkout';
import Report from './pages/Report';
import PdfPreview from './pages/PdfPreview';
import Chat from './pages/Chat';
import VolunteerList from './pages/VolunteerList';
import UniversityDetail from './pages/UniversityDetail';
import JiangsuResults from './pages/JiangsuResults';
import type { ToastMessage } from './types';

// Scroll to top on route change
function ScrollToTop() {
  const { pathname } = window.location;
  const cleanPath = pathname.replace(/^#\//, '');
  const prevPath = (window as any).__prevPath;
  if (prevPath !== cleanPath) {
    (window as any).__prevPath = cleanPath;
    setTimeout(() => window.scrollTo(0, 0), 0);
  }
  return null;
}

// Animated routes wrapper
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <Routes location={location}>
          {/* Specific routes BEFORE wildcard — pdf-preview must match first */}
          <Route path="/report/pdf-preview/:reportId" element={<PdfPreview />} />
          <Route path="/chat" element={<Chat />} />

          <Route element={<MainLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/calculator" element={<Calculator />} />
            <Route path="/preview" element={<Preview />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/volunteer-list" element={<VolunteerList />} />
            <Route path="/university/:slug" element={<UniversityDetail />} />
            <Route path="/jiangsu-results" element={<JiangsuResults />} />
            <Route path="/report" element={<Report />} />
            <Route path="/report/:reportId" element={<Report />} />
          </Route>
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((type: ToastMessage['type'], message: string, duration = 4000) => {
    const id = `toast_${Date.now()}`;
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <HashRouter>
      <ScrollToTop />
      {/* Noise overlay */}
      <div className="noise-overlay" />
      <AnimatedRoutes />
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </HashRouter>
  );
}
