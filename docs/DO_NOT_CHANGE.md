# 择境 ZENPATH — 禁止修改文件清单

> 本文档定义了项目中哪些文件/目录禁止或谨慎修改。
> 分为 S/A/B/C 四个等级，S 级最严格。
> 任何 Agent 或开发者在修改文件前必须查阅本文档。

---

## S 级：绝对禁止未经明确确认修改

以下文件/目录在任何情况下都不得修改，除非用户在当前会话中明确说"可以修改 XXX"。

| 路径 | 原因 |
|------|------|
| `.env` | 含 API key（DeepSeek/MIMO）和数据库连接串 |
| `zenpath-nginx.conf` | 含真实服务器 IP 和部署路径 |
| `backend/*.db` | 生产数据库文件 |
| `backend/app/*.db` | 应用级数据库文件 |
| `backend/app/models/models.py` | ORM 模型，修改会影响数据库结构 |
| `backend/app/core/config.py` | 核心配置（API key 读取、数据库 URL、CORS） |
| `backend/app/core/database.py` | 数据库连接初始化 |
| `backend/app/routes/session.py` | 登录鉴权逻辑（匿名会话、token 生成） |
| `backend/app/routes/order.py` | 支付订单逻辑（价格、订单号生成） |
| `backend/app/routes/membership.py` | 会员系统（订阅、权益验证） |
| `backend/app/services/membership_service.py` | 会员权益判断核心逻辑 |
| `backend/app/services/report_permission_service.py` | 报告生成权限控制 |
| `data/` | 原始数据（3.5GB），含 RAG 知识库、高考数据、省份数据 |
| `rag_output/` | RAG 生成产物（360MB） |
| `assets/logos/` | CDN 校徽资源（448MB） |
| `.gitignore` | Git 排除规则，修改不当会导致敏感文件泄露 |

---

## A 级：必须先只读分析，再请求确认

以下文件/目录修改前必须：
1. 先读取并分析当前内容
2. 输出修改计划和影响范围
3. 等待用户确认后才能修改

| 路径 | 原因 |
|------|------|
| `frontend/tailwind.config.js` | 设计系统 token，改了全站样式崩 |
| `frontend/src/App.tsx` | 路由入口，改了全站路由崩 |
| `frontend/src/components/layout/` | Navbar、Footer、MainLayout，全局布局 |
| `frontend/src/index.css` | 全局样式 |
| `frontend/vite.config.ts` | 构建配置、API proxy |
| `frontend/package.json` | 依赖声明，新增依赖需确认 |
| `backend/app/main.py` | FastAPI 入口，路由注册、中间件 |
| `backend/app/schemas/schemas.py` | API 数据模型，改了前后端接口全崩 |
| `backend/migrations/` | 数据库迁移脚本 |
| `backend/requirements.txt` | Python 依赖 |
| `backend/app/services/llm_client.py` | LLM 调用客户端，改了 AI 功能全崩 |
| `backend/rag/` | RAG 处理管线（爬虫、切片、检索、生成） |

---

## B 级：允许修改但必须说明影响范围

以下文件/目录可以修改，但必须在报告中说明：
- 修改了什么
- 影响了哪些页面/功能
- 是否需要回归测试

| 路径 | 说明 |
|------|------|
| `frontend/src/pages/` | 页面组件，每个页面相对独立 |
| `frontend/src/components/common/` | 通用组件（Button、Modal、Toast 等） |
| `frontend/src/components/charts/` | 图表组件 |
| `frontend/src/components/panels/` | 面板组件 |
| `frontend/src/components/school/` | 学校相关组件 |
| `frontend/src/services/` | API 调用层 |
| `frontend/src/hooks/` | 自定义 Hook |
| `frontend/src/config/` | 前端配置（会员套餐等） |
| `frontend/src/types/` | TypeScript 类型定义 |
| `frontend/src/utils/` | 工具函数 |
| `backend/app/routes/` | API 路由（session/order/membership 除外） |
| `backend/app/services/` | 业务服务（membership/permission 除外） |
| `backend/seed_data/` | 数据导入脚本 |
| `scripts/` | 工具脚本 |
| `tests/` | 测试脚本 |

---

## C 级：普通可修改文件

以下文件/目录属于基础设施，可以正常修改：

| 路径 | 说明 |
|------|------|
| `docs/` | 项目文档（不含 dyad prompt） |
| `specs/` | 规格模板 |
| `deploy/nginx/` | 部署配置模板 |
| `.hermes/prompts/` | Agent prompt |
| `.github/` | GitHub 模板和 CI（后续阶段新增） |
| `playwright.config.ts` | Playwright 配置（后续阶段新增） |
| `e2e/` | E2E 测试（后续阶段新增） |

---

## 快速查询

修改文件前，用以下方式快速判断等级：

```bash
# 在项目根目录执行
grep -r "你的文件路径" docs/DO_NOT_CHANGE.md
```

如果不确定，默认按 **A 级**处理：先分析、再确认。

---

## 更新记录

| 日期 | 变更 |
|------|------|
| 2026-06-29 | 初始版本，基于项目现状分析 |
