import { useState } from 'react';
import { motion } from 'framer-motion';
import { URONDA_LOGO_MAP } from '../../data/urongda_logo_map';
import { resolveSchoolName } from '../../utils/schoolNameResolver';

// ========== Component ==========

interface SchoolBadgeProps {
  slug: string;
  name: string;
  size?: number;
  className?: string;
}

function getInitials(name: string): string {
  return name.slice(0, 2);
}

export default function SchoolBadge({ slug, name, size = 40, className = '' }: SchoolBadgeProps) {
  const [imgError, setImgError] = useState(false);
  const [useFallback, setUseFallback] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);

  // Resolve school name to logo name via rule-based matching
  const resolution = resolveSchoolName(name);
  const logoName = resolution.logoName;

  // Look up the resolved logo name in the Urongda map
  const urongdaSlug = logoName ? URONDA_LOGO_MAP[logoName] : null;
  const urongdaUrl = urongdaSlug ? `/urongda-logos/${urongdaSlug}_logo_128.png` : null;

  // SVG path (try both original name and resolved logo name)
  const svgUrl = logoName
    ? `/logos/${encodeURIComponent(logoName)}_logo_full.svg`
    : `/logos/${encodeURIComponent(name)}_logo_full.svg`;

  // ═══ Urongda PNG try ═══
  if (urongdaUrl && !useFallback) {
    return (
      <motion.div
        className={`shrink-0 relative ${className}`}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        style={{ width: size, height: size }}
      >
        {!imgLoaded && (
          <div
            className="absolute inset-0 rounded-full skeleton"
            style={{ width: size, height: size }}
          />
        )}
        <img
          src={urongdaUrl}
          alt={name}
          className={`rounded-full object-contain bg-white transition-opacity duration-300 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`}
          style={{ width: size, height: size }}
          onLoad={() => setImgLoaded(true)}
          onError={() => { setUseFallback(true); setImgLoaded(true); }}
        />
      </motion.div>
    );
  }

  // ═══ SVG try ═══
  if (!imgError) {
    return (
      <motion.div
        className={`shrink-0 relative ${className}`}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        style={{ width: size, height: size }}
      >
        {!imgLoaded && (
          <div
            className="absolute inset-0 rounded-full skeleton"
            style={{ width: size, height: size }}
          />
        )}
        <img
          src={svgUrl}
          alt={name}
          className={`rounded-full object-contain bg-white transition-opacity duration-300 ${imgLoaded ? 'opacity-100' : 'opacity-0'}`}
          style={{ width: size, height: size, padding: 2 }}
          onLoad={() => setImgLoaded(true)}
          onError={() => { setImgError(true); setImgLoaded(true); }}
        />
      </motion.div>
    );
  }

  // ═══ Fallback: initials ═══
  return (
    <motion.div
      className="rounded-full flex items-center justify-center shrink-0 border-[0.5px] border-[#E0D8CC]/50"
      style={{
        width: size,
        height: size,
        backgroundColor: '#1A2E22',
      }}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <span
        className="font-serif text-white"
        style={{ fontSize: Math.max(size * 0.38, 10) }}
      >
        {getInitials(name)}
      </span>
    </motion.div>
  );
}
