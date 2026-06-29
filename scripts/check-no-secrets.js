#!/usr/bin/env node
/**
 * check-no-secrets.js
 * Scans tracked source files for potential secret patterns.
 * Does NOT scan .env files. Does NOT display secret values.
 * Run: node scripts/check-no-secrets.js
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SECRET_PATTERNS = [
  { regex: /sk-[a-zA-Z0-9]{20,}/, label: 'OpenAI/DeepSeek API key (sk-...)' },
  { regex: /['"](sk-[a-zA-Z0-9]{20,})['"]/, label: 'Hardcoded API key string' },
];

// Patterns that are ALLOWED (environment variable reads)
const ALLOWED_PATTERNS = [
  /os\.environ\.get\(/,
  /os\.getenv\(/,
  /process\.env\./,
  /os\.environ\[.*\]/,
  /= *['"]{0,2}['"]{0,2}$/,  // empty string default
];

// Patterns that are suspicious but need context
const SUSPICIOUS_PATTERNS = [
  { regex: /api_key\s*=\s*['"][^'"]{8,}['"]/, label: 'Hardcoded api_key assignment' },
  { regex: /API_KEY\s*=\s*['"][^'"]{8,}['"]/, label: 'Hardcoded API_KEY assignment' },
  { regex: /password\s*=\s*['"][^'"]{4,}['"]/, label: 'Hardcoded password' },
  { regex: /secret\s*=\s*['"][^'"]{8,}['"]/, label: 'Hardcoded secret' },
  { regex: /Bearer\s+[a-zA-Z0-9._-]{20,}/, label: 'Hardcoded Bearer token' },
];

const SOURCE_EXTENSIONS = new Set([
  '.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.yml', '.yaml', '.toml', '.cfg', '.conf',
]);

console.log('=== check-no-secrets ===');
console.log('Scanning source files for secret patterns...\n');

let trackedFiles;
try {
  trackedFiles = execSync('git ls-files', { encoding: 'utf8' }).trim().split('\n').filter(Boolean);
} catch (e) {
  console.error('❌ Failed to run git ls-files:', e.message);
  process.exit(1);
}

let findings = 0;

for (const file of trackedFiles) {
  // Skip .env, .env.*, binary files, lock files
  if (path.basename(file).startsWith('.env')) continue;
  if (file.endsWith('.lock')) continue;
  if (file.endsWith('.png') || file.endsWith('.svg') || file.endsWith('.ico')) continue;

  const ext = path.extname(file);
  if (!SOURCE_EXTENSIONS.has(ext)) continue;

  let content;
  try {
    content = fs.readFileSync(file, 'utf8');
  } catch (e) {
    continue;
  }

  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    // Check for definite secrets
    for (const p of SECRET_PATTERNS) {
      if (p.regex.test(line)) {
        const isAllowed = ALLOWED_PATTERNS.some(a => a.test(line));
        if (!isAllowed) {
          const match = line.match(/['"]([^'"]*)['"]/);
          const val = match ? match[1] : '';
          if (!val || val === '***' || val.includes('your_') || val.includes('xxx') || val.includes('placeholder') || val.includes('here')) {
            continue;
          }
          console.log(`  ⚠️  ${file}:${lineNum} — ${p.label}`);
          findings++;
        }
      }
    }

    // Check for suspicious patterns
    for (const p of SUSPICIOUS_PATTERNS) {
      if (p.regex.test(line)) {
        const isAllowed = ALLOWED_PATTERNS.some(a => a.test(line));
        if (!isAllowed) {
          const match = line.match(/=\s*['"]([^'"]*)['"]/);
          const val = match ? match[1] : '';
          if (!val || val === '***' || val.includes('your_') || val.includes('xxx') || val.includes('placeholder') || val.includes('here')) {
            continue;
          }
          console.log(`  ⚠️  ${file}:${lineNum} — ${p.label}`);
          findings++;
        }
      }
    }
  }
}

if (findings > 0) {
  console.log(`\n⚠️  Found ${findings} potential secret(s). Review manually.`);
  console.log('Note: false positives are possible. Check each finding.');
  process.exit(1);
} else {
  console.log(`✅ No obvious secrets found in ${trackedFiles.length} tracked files.`);
  process.exit(0);
}
