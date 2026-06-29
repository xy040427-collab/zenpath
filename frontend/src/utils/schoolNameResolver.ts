/**
 * School Name Resolver — resolves school names to logo names via
 * rule-based normalization + canonical name matching.
 *
 * Principles:
 * - Never modify the original school_name
 * - No hardcoded per-school mappings
 * - Automatic matching via canonical name set + safe suffix rules
 * - Risk blocking for independent/vocational colleges
 * - Fallback gracefully to initials/placeholder
 */

import canonicalSchoolNamesJson from '../data/canonical_school_names.json';

// ═══════════════════════════════════════════════
//  Types
// ═══════════════════════════════════════════════

export type LogoMatchType =
  | 'exact'
  | 'normalized_exact'
  | 'cleaned_exact'
  | 'canonical_prefix'
  | 'parent_by_suffix_rule'
  | 'fallback';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface SchoolNameResolution {
  /** Original name — NEVER modified */
  originalName: string;
  /** Display name = originalName (unchanged for UI) */
  displayName: string;
  /** Normalized name (whitespace collapsed, brackets unified) */
  normalizedName: string;
  /** Name matched to a logo (null if fallback) */
  logoName: string | null;
  /** How the match was found */
  logoMatchType: LogoMatchType;
  /** Confidence level */
  confidence: ConfidenceLevel;
  /** Any warnings about the match */
  warnings: string[];
}

// ═══════════════════════════════════════════════
//  Canonical school names (from data sources)
// ═══════════════════════════════════════════════

const canonicalSchoolNames: string[] = canonicalSchoolNamesJson as string[];

// Build fast lookup sets
const canonicalSet = new Set(canonicalSchoolNames);
// Sort by length descending for longest-prefix matching
const canonicalSorted = [...canonicalSchoolNames].sort((a, b) => b.length - a.length);

// ═══════════════════════════════════════════════
//  Noise patterns to strip for matching only
// ═══════════════════════════════════════════════

const NOISE_PARENTHETICALS = [
  /[（(]中外合作(?:办学)?[）)]/g,
  /[（(]地方专项(?:计划)?[）)]/g,
  /[（(]高校专项(?:计划)?[）)]/g,
  /[（(]国家专项(?:计划)?[）)]/g,
  /[（(](?:边防子女)?预科班[）)]/g,
  /[（(]联合培养[）)]/g,
  /[（(]较高收费[）)]/g,
  /[（(]单列专业[）)]/g,
  /[（(]护理学[）)]/g,
  /[（(]民办[）)]/g,
];

const NOISE_TRAILING = [
  /\s*物理类$/,
  /\s*历史类$/,
];

// ═══════════════════════════════════════════════
//  Safe suffixes — allowed for parent matching
// ═══════════════════════════════════════════════

const SAFE_SUFFIXES: readonly string[] = [
  '医学院',
  '医学部',
  '上海医学院',
  '临床医学院',
  '校区',
  '威海校区',
  '深圳校区',
  '苏州校区',
  '宣城校区',
  '沙河校区',
  '盘锦校区',
  '宏福校区',
  '分校',
  '威海分校',
  '秦皇岛分校',
];

// ═══════════════════════════════════════════════
//  Risk blocking — independent/vocational colleges
// ═══════════════════════════════════════════════

const RISK_WORDS: readonly string[] = [
  '独立学院',
  '应用技术学院',
  '成贤学院',
  '金陵学院',
  '中北学院',
  '现代文理学院',
  '城市学院',
  '科技学院',      // be careful — many public 科技学院 exist
  '商学院',        // same — but in context of independent college detection
  '国际学院',
  '国际大学',
  '职业技术大学',
  '职业学院',
];

// High-risk independent colleges — exact block for parent matching
// These are NOT hardcoded per-school mappings; they are risk-pattern blocks.
const INDEPENDENT_COLLEGE_RISK_PATTERNS: readonly RegExp[] = [
  // Independent colleges named after parent university
  /南京大学金陵学院/,
  /东南大学成贤学院/,
  /南京师范大学中北学院/,
  /苏州大学应用技术学院/,
  /南京理工大学紫金学院/,
  /南京航空航天大学金城学院/,
  /南京信息工程大学滨江学院/,
  /南京邮电大学通达学院/,
  /南京财经大学红山学院/,
  /南京审计大学金审学院/,
  /中国传媒大学南广学院/,
  /南京工业大学浦江学院/,
  /江苏大学京江学院/,
  /扬州大学广陵学院/,
  /南通大学杏林学院/,
  /常州大学怀德学院/,
  // Other well-known independent colleges
  /浙江大学城市学院/,
  /浙江大学宁波理工学院/,
  /厦门大学嘉庚学院/,
  /北京理工大学珠海学院/,
  /吉林大学珠海学院/,
  /四川大学锦城学院/,
  /四川大学锦江学院/,
  /电子科技大学成都学院/,
  /南开大学滨海学院/,
  /天津大学仁爱学院/,
  /北京科技大学天津学院/,
  /北京交通大学海滨学院/,
  /河北工业大学城市学院/,
  /燕山大学里仁学院/,
  // Independent Sino-foreign universities (independent legal entities)
  /西交利物浦大学/,
  /上海纽约大学/,
  /昆山杜克大学/,
  /宁波诺丁汉大学/,
  /温州肯恩大学/,
  /广东以色列理工学院/,
  /深圳北理莫斯科大学/,
  /香港中文大学（深圳）/,
  /香港科技大学（广州）/,
  /北京师范大学-香港浸会大学联合国际学院/,
];

// ═══════════════════════════════════════════════
//  Utility: normalize brackets
// ═══════════════════════════════════════════════

function normalizeBrackets(name: string): string {
  // Unify all parentheses to half-width for matching consistency
  return name
    .replace(/（/g, '(')
    .replace(/）/g, ')');
}

// ═══════════════════════════════════════════════
//  normalizeSchoolName()
// ═══════════════════════════════════════════════

export function normalizeSchoolName(rawName: string): string {
  if (!rawName) return '';

  let result = rawName.trim();

  // Collapse multiple spaces
  result = result.replace(/\s+/g, ' ');

  // Remove invisible characters (zero-width, BOM, etc.)
  result = result.replace(/[\u200B-\u200D\uFEFF]/g, '');

  // Normalize brackets for consistency
  result = normalizeBrackets(result);

  return result;
}

// ═══════════════════════════════════════════════
//  cleanNameForMatching()
// ═══════════════════════════════════════════════

export function cleanNameForMatching(name: string): string {
  let result = normalizeSchoolName(name);

  // Strip noise parentheticals
  for (const pattern of NOISE_PARENTHETICALS) {
    result = result.replace(pattern, '');
  }

  // Strip noise trailing suffixes
  for (const pattern of NOISE_TRAILING) {
    result = result.replace(pattern, '');
  }

  // Collapse spaces again after removals
  result = result.replace(/\s+/g, ' ').trim();

  return result;
}

// ═══════════════════════════════════════════════
//  isIndependentCollege()
// ═══════════════════════════════════════════════

function isIndependentCollege(name: string): boolean {
  for (const pattern of INDEPENDENT_COLLEGE_RISK_PATTERNS) {
    if (pattern.test(name)) return true;
  }
  return false;
}

// ═══════════════════════════════════════════════
//  findLongestCanonicalPrefix()
// ═══════════════════════════════════════════════

function findLongestCanonicalPrefix(name: string): string | null {
  // Find all canonical names that are prefixes of name
  const candidates: string[] = [];
  for (const canonical of canonicalSorted) {
    if (name.startsWith(canonical)) {
      candidates.push(canonical);
    }
  }
  if (candidates.length === 0) return null;

  // Return longest match
  candidates.sort((a, b) => b.length - a.length);
  return candidates[0];
}

// ═══════════════════════════════════════════════
//  hasSafeSuffix()
// ═══════════════════════════════════════════════

function hasSafeSuffix(name: string, prefix: string): boolean {
  // The remainder after removing the prefix
  const remainder = name.slice(prefix.length);

  if (!remainder) return false;

  // Check if the remainder is exactly one of the safe suffixes
  // or if it's a parenthesized safe suffix like "(深圳)" after stripping brackets
  const cleanRemainder = remainder
    .replace(/^[（(]/, '')
    .replace(/[）)]$/, '');

  for (const suffix of SAFE_SUFFIXES) {
    if (remainder === suffix) return true;
    if (cleanRemainder === suffix) return true;
  }

  return false;
}

// ═══════════════════════════════════════════════
//  resolveSchoolName()
// ═══════════════════════════════════════════════

export function resolveSchoolName(
  rawName: string,
  logoSchoolNames?: string[],
): SchoolNameResolution {
  const warnings: string[] = [];

  // Clean the input name
  const normalizedName = normalizeSchoolName(rawName);
  const cleanedName = cleanNameForMatching(rawName);

  // Use provided logo names or the full canonical set
  const logoSet = logoSchoolNames
    ? new Set(logoSchoolNames)
    : canonicalSet;

  // Step 1: Exact match on original name
  if (logoSet.has(rawName)) {
    return {
      originalName: rawName,
      displayName: rawName,
      normalizedName,
      logoName: rawName,
      logoMatchType: 'exact',
      confidence: 'high',
      warnings,
    };
  }

  // Step 2: Exact match on normalized name
  if (normalizedName !== rawName && logoSet.has(normalizedName)) {
    return {
      originalName: rawName,
      displayName: rawName,
      normalizedName,
      logoName: normalizedName,
      logoMatchType: 'normalized_exact',
      confidence: 'high',
      warnings,
    };
  }

  // Step 3: Exact match on cleaned name
  if (cleanedName !== normalizedName && cleanedName !== rawName && logoSet.has(cleanedName)) {
    return {
      originalName: rawName,
      displayName: rawName,
      normalizedName,
      logoName: cleanedName,
      logoMatchType: 'cleaned_exact',
      confidence: 'high',
      warnings,
    };
  }

  // Step 4: Longest canonical prefix match
  // Try on cleaned name first, then normalized, then raw
  for (const candidateName of [cleanedName, normalizedName, rawName]) {
    // Risk check: if this is a known independent college, skip parent matching
    if (isIndependentCollege(candidateName)) {
      warnings.push(`Risk blocked: "${candidateName}" is an independent college — will not match to parent university`);
      break; // Don't attempt parent matching
    }

    const prefix = findLongestCanonicalPrefix(candidateName);
    if (prefix && logoSet.has(prefix)) {
      // Verify the suffix is safe
      if (hasSafeSuffix(candidateName, prefix)) {
        return {
          originalName: rawName,
          displayName: rawName,
          normalizedName,
          logoName: prefix,
          logoMatchType: 'canonical_prefix',
          confidence: 'high',
          warnings,
        };
      }
      // Prefix found but suffix is not in safe list — might be independent college
      // Only log warning, still try step 5
      warnings.push(
        `Canonical prefix "${prefix}" found but suffix not in safe list — falling through to step 5`,
      );
    }
  }

  // Step 5: Parent-by-suffix-rule matching
  // Try cleaning campus/parenthetical content and matching
  for (const candidateName of [cleanedName, normalizedName]) {
    // Risk check
    if (isIndependentCollege(candidateName)) {
      warnings.push(`Risk blocked: "${candidateName}" is an independent college`);
      break;
    }

    // Strip parenthetical content: "大学(校区)" → "大学"
    const strippedParens = candidateName.replace(/[（(][^）)]*[）)]/g, '').trim();

    if (strippedParens !== candidateName && logoSet.has(strippedParens)) {
      return {
        originalName: rawName,
        displayName: rawName,
        normalizedName,
        logoName: strippedParens,
        logoMatchType: 'parent_by_suffix_rule',
        confidence: 'high',
        warnings,
      };
    }

    // Try removing the parenthesized suffix and checking if the prefix matches a canonical
    // e.g. "大连理工大学(盘锦校区)" → strip "(盘锦校区)" → "大连理工大学" → match
    const afterStrip = candidateName.replace(/[（(][^）)]*[）)]$/, '').trim();
    if (afterStrip !== candidateName && logoSet.has(afterStrip)) {
      return {
        originalName: rawName,
        displayName: rawName,
        normalizedName,
        logoName: afterStrip,
        logoMatchType: 'parent_by_suffix_rule',
        confidence: 'high',
        warnings,
      };
    }
  }

  // Step 6: Fallback — no logo matched
  warnings.push(`No logo matched for "${rawName}" — using fallback`);
  return {
    originalName: rawName,
    displayName: rawName,
    normalizedName,
    logoName: null,
    logoMatchType: 'fallback',
    confidence: 'low',
    warnings,
  };
}

// ═══════════════════════════════════════════════
//  Exports for audit/reporting
// ═══════════════════════════════════════════════

export function getCanonicalSchoolNames(): string[] {
  return canonicalSchoolNames;
}

export function getLogoSchoolNames(): string[] {
  return Object.keys(canonicalSet);
}

export function isInLogoSet(name: string): boolean {
  return canonicalSet.has(name);
}
