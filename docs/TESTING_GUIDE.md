# 择境 ZENPATH — 测试与验收指南

> 本文档定义了项目的测试、构建和验收标准。
> Agent 每次修改后必须按本文档执行验证。

---

## 一、环境信息

| 项目 | 值 |
|------|-----|
| 前端目录 | `frontend/` |
| 后端目录 | `backend/` |
| 前端端口 | 5173（dev）/ 3457（vite proxy 目标） |
| 后端端口 | 8000（uvicorn） |
| 数据库 | SQLite: `backend/gaokao.db` |
| Python | 3.13 |
| Node.js | 18+ |

---

## 二、必须运行的命令

### 前端构建（每次修改前端后必须运行）

```bash
cd frontend && npm run build
```

- 包含 TypeScript 类型检查（`tsc`）和 Vite 构建
- 如果报错，**任务未完成**
- 常见失败原因：类型错误、导入路径错误、缺少依赖

### 前端类型检查（可选，build 已包含）

```bash
cd frontend && npm run type-check
```

### 前端开发启动（页面验收时使用）

```bash
cd frontend && npm run dev
```

### 后端启动（后端修改后或页面验收时使用）

```bash
cd backend && uvicorn app.main:app --reload --port 3458
```

- 默认端口 8000，但 Vite proxy 配置指向 3458
- 如果端口冲突，说明已有实例在运行

---

## 三、当前测试状态

| 能力 | 状态 | 说明 |
|------|------|------|
| 前端 lint | ❌ 未配置 | 无 ESLint 配置 |
| 前端单元测试 | ❌ 未配置 | 无 vitest/jest |
| 后端 lint | ❌ 未配置 | 无 ruff/flake8 |
| 后端单元测试 | ❌ 未配置 | 无 pytest 配置 |
| E2E 测试 | ❌ 未配置 | 无 Playwright |
| CI | ❌ 未配置 | 无 GitHub Actions |

**在测试体系未完善前，Agent 至少必须运行 build。**

---

## 四、页面验收流程

每次前端修改后，必须执行以下验收：

### 4.1 启动验证

1. `cd frontend && npm run build` — 构建通过
2. `cd frontend && npm run dev` — 开发服务器启动
3. 浏览器打开 `http://localhost:5173` — 页面可访问

### 4.2 核心页面检查

以下页面必须逐一检查：

| 页面 | 路由 | 检查项 |
|------|------|--------|
| 首页 | `/` | 无白屏、标题可见、导航可见 |
| 聊天 | `/chat` | 页面可打开、输入框可见 |
| 计算器 | `/calculator` | 页面可打开 |
| 定价 | `/pricing` | 套餐卡片可见 |
| 报告 | `/report` | 页面可打开（需要登录态） |
| 大学详情 | `/university/:id` | 页面可打开 |

### 4.3 检查清单

- [ ] 无白屏（body 有内容）
- [ ] 导航栏可见且可点击
- [ ] 核心按钮可点击（不 disabled、不无响应）
- [ ] 路由跳转正常（点击导航链接能跳转）
- [ ] 布局无明显跑偏（不对齐、溢出、重叠）
- [ ] 颜色符合品牌规范（墨绿+米色）
- [ ] 移动端基本可用（缩小浏览器窗口检查）

### 4.4 后端验收

1. `cd backend && uvicorn app.main:app --port 3458` — 启动成功
2. 访问 `http://localhost:3458/docs` — Swagger 文档可见
3. 测试关键 API：
   - `GET /api/v1/config/plans` — 返回套餐列表
   - `POST /api/v1/sessions/anonymous` — 创建会话

---

## 五、常见失败原因

| 现象 | 可能原因 | 排查方式 |
|------|---------|---------|
| build 报 TS 类型错误 | 新代码类型不对 | 看报错行号，修类型 |
| build 报模块找不到 | 导入路径错误或缺依赖 | 检查 import 路径 |
| 页面白屏 | 运行时错误 | 打开浏览器控制台看报错 |
| 按钮不可点击 | 事件绑定缺失或 disabled | 检查 onClick 和 disabled 属性 |
| 路由 404 | 路由配置错误 | 检查 App.tsx 路由表 |
| API 报 CORS | 后端 CORS 配置 | 检查 config.py cors_origins |
| API 500 | 后端代码异常 | 看 uvicorn 终端日志 |
| 数据库锁定 | 多进程同时写 SQLite | 关闭多余后端实例 |

---

## 六、Agent 修改后的最低验证

| 修改类型 | 最低验证 |
|---------|---------|
| 前端页面/组件 | `npm run build` + 页面打开无白屏 |
| 前端样式 | `npm run build` + 视觉检查 |
| 前端路由 | `npm run build` + 路由跳转测试 |
| 后端 API | 后端启动 + Swagger 可访问 |
| 后端服务 | 后端启动 + 相关 API 调用 |
| 配置文件 | 相关功能验证 |
| 文档 | 无验证要求 |

---

## 七、命令不存在时的处理

如果运行某个命令时发现不存在（如 `npm run lint`、`npx playwright test`）：

1. **如实报告**："命令 XXX 不存在"
2. **不要编造**结果
3. **不要跳过**验证
4. **在报告中说明**：哪些验证能做、哪些不能做

---

## 八、后续接入计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 5 | GitHub Actions CI | 待实施 |
| 阶段 6 | Playwright E2E 测试 | 待实施 |
| 阶段 7 | 自动检查脚本 | 待实施 |
| 未来 | ESLint + ruff 配置 | 待规划 |
| 未来 | vitest / pytest | 待规划 |
