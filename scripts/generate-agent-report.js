#!/usr/bin/env node
/**
 * generate-agent-report.js
 * Generates a basic Agent execution report from Git state.
 * Run: node scripts/generate-agent-report.js
 */

const { execSync } = require('child_process');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8' }).trim();
  } catch (e) {
    return `(error: ${e.message.split('\n')[0]})`;
  }
}

console.log('# Agent 执行报告（自动生成）');
console.log(`\n生成时间: ${new Date().toISOString()}\n`);

// Branch & Commit
console.log('## 基本信息');
console.log(`- **当前分支**: ${run('git branch --show-current')}`);
console.log(`- **最近 commit**: ${run('git log --oneline -1')}`);
console.log(`- **工作区状态**: ${run('git status --short') || '干净'}`);

// Recent changes
console.log('\n## 最近修改');
const recentFiles = run('git diff --name-only HEAD~1 2>/dev/null || echo "N/A"');
console.log(`\n最近一次 commit 修改的文件:\n\`\`\`\n${recentFiles}\n\`\`\``);

// Forbidden files check
console.log('\n## 安全检查');
try {
  execSync('node scripts/check-forbidden-files.js', { stdio: 'pipe' });
  console.log('- ✅ 无禁止文件被追踪');
} catch (e) {
  console.log('- ❌ 发现禁止文件被追踪');
}

// Secret check
try {
  execSync('node scripts/check-no-secrets.js', { stdio: 'pipe' });
  console.log('- ✅ 无明显密钥泄露');
} catch (e) {
  console.log('- ⚠️ 发现疑似密钥，需要人工复查');
}

// Summary
console.log('\n## 建议下一步');
console.log('1. 检查 CI 是否通过');
console.log('2. 检查页面是否正常');
console.log('3. 检查是否有未完成项');
console.log('4. 决定是否合并');
