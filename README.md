# 择境 ZENPATH

> 择善境，行远路。AI 智能高考志愿填报系统。

输入分数和偏好，生成科学可依的冲稳保方案。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS 3 |
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| AI | DeepSeek / MIMO (OpenAI SDK) |
| RAG | 自建知识库 + 向量检索 |

## 快速启动

```bash
# 前端
cd frontend
npm install
npm run dev    # http://localhost:5173

# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3458
```

## 构建

```bash
cd frontend && npm run build
```

## 测试

```bash
# Playwright E2E
cd frontend && npx playwright test

# 安全检查
node scripts/check-forbidden-files.js
node scripts/check-no-secrets.js
```

## 项目规则

开发前必须阅读：

- [项目总规则](docs/PROJECT_RULES.md)
- [禁止修改清单](docs/DO_NOT_CHANGE.md)
- [UI 风格规范](docs/STYLE_GUIDE.md)
- [测试验收指南](docs/TESTING_GUIDE.md)
- [安全策略](docs/SECURITY_POLICY.md)
- [AI Agent 工作流](docs/AI_AGENT_WORKFLOW.md)
- [黄金路径](docs/GOLDEN_PATH.md)

## 目录结构

```
├── frontend/          # React 前端
├── backend/           # FastAPI 后端
├── specs/             # 功能规格
├── docs/              # 项目文档和规则
├── scripts/           # 工具脚本
├── tests/             # 测试
├── deploy/            # 部署配置模板
└── .github/           # CI 和模板
```

## 许可

私有项目。
