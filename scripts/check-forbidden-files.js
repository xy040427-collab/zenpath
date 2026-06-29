#!/usr/bin/env node
/**
 * check-forbidden-files.js
 * Checks that no forbidden files are tracked by Git.
 * Run: node scripts/check-forbidden-files.js
 */

const { execSync } = require('child_process');

const FORBIDDEN_PATTERNS = [
  { pattern: /^\.env$/, exception: /^\.env\.example$/, label: '.env (secret)' },
  { pattern: /^\.env\./, exception: /^\.env\.example$/, label: '.env.* (secret)' },
  { pattern: /\.(db|sqlite|sqlite3)$/, exception: null, label: 'database file' },
  { pattern: /^data\//, exception: null, label: 'data/ (large raw data)' },
  { pattern: /^rag_output\//, exception: null, label: 'rag_output/ (generated)' },
  { pattern: /^backend\/rag_output\//, exception: null, label: 'backend/rag_output/' },
  { pattern: /^assets\/logos\//, exception: null, label: 'assets/logos/ (CDN)' },
  { pattern: /^frontend\/public\/logos\//, exception: null, label: 'frontend/public/logos/' },
  { pattern: /^frontend\/public\/urongda-logos\//, exception: null, label: 'frontend/public/urongda-logos/' },
  { pattern: /^node_modules\//, exception: null, label: 'node_modules/' },
  { pattern: /^frontend\/node_modules\//, exception: null, label: 'frontend/node_modules/' },
  { pattern: /^frontend\/dist\//, exception: null, label: 'frontend/dist/' },
  { pattern: /^dist\//, exception: null, label: 'dist/' },
  { pattern: /^zenpath-nginx\.conf$/, exception: null, label: 'real deploy config' },
  { pattern: /\.(docx|pdf|pptx|zip)$/, exception: /deploy\/nginx\/zenpath-nginx\.example\.conf$/, label: 'binary document' },
];

console.log('=== check-forbidden-files ===');
console.log('Scanning Git tracked files...\n');

let trackedFiles;
try {
  trackedFiles = execSync('git ls-files', { encoding: 'utf8' }).trim().split('\n').filter(Boolean);
} catch (e) {
  console.error('❌ Failed to run git ls-files:', e.message);
  process.exit(1);
}

let violations = 0;

for (const file of trackedFiles) {
  for (const rule of FORBIDDEN_PATTERNS) {
    if (rule.pattern.test(file)) {
      if (rule.exception && rule.exception.test(file)) continue;
      console.log(`  ❌ ${rule.label}: ${file}`);
      violations++;
    }
  }
}

if (violations > 0) {
  console.log(`\n❌ Found ${violations} forbidden file(s) tracked by Git.`);
  process.exit(1);
} else {
  console.log(`✅ All ${trackedFiles.length} tracked files are clean. No forbidden files found.`);
  process.exit(0);
}
