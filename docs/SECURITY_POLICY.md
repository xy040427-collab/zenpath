# 择境 ZENPATH — 安全策略

> 本文档定义了项目的安全规则。
> 涉及安全的变更必须单独 PR，必须人工复查。

---

## 一、密钥管理

### 绝对规则

| 编号 | 规则 |
|------|------|
| SEC-01 | `.env` 不进入 Git（已在 .gitignore 排除） |
| SEC-02 | API key 不写入代码，只能从环境变量读取 |
| SEC-03 | 不允许在日志中输出 API key |
| SEC-04 | 不允许在错误响应中暴露内部路径或密钥 |
| SEC-05 | 不允许展示密钥原文（包括在对话、报告、PR 描述中） |

### 当前密钥来源

所有密钥通过 `backend/app/core/config.py` 从环境变量读取：

- `DEEPSEEK_API_KEY` — DeepSeek API
- `MIMO_API_KEY` — MIMO API
- `DATABASE_URL` — 数据库连接串

**代码中只允许 `os.environ.get("KEY")` 或 pydantic-settings 读取，不允许硬编码。**

### 历史安全事件

`backend/app/services/school_detail_generator.py` 在早期本地 commit 中曾出现硬编码 API key。该问题已通过 `git-filter-repo` 清理历史，并将代码改为从环境变量读取。任何硬编码 API key 均视为严重安全问题。即使历史已清理，相关 key 仍必须在平台控制台轮换。

---

## 二、敏感文件保护

### 不得提交到 Git 的文件

| 文件 | 原因 |
|------|------|
| `.env` | 含 API key |
| `*.db` | 含用户数据、会话、订单 |
| `zenpath-nginx.conf` | 含真实服务器 IP |
| `data/` | 3.5GB 原始数据 |
| `rag_output/` | RAG 生成产物 |
| `assets/logos/` | CDN 资源 |

### 不得修改的文件（无用户确认）

参见 `DO_NOT_CHANGE.md` S 级清单。

---

## 三、认证与授权

### 当前认证机制

- 匿名会话：`POST /api/v1/sessions/anonymous` 生成 session_token
- token 存储在数据库 sessions 表
- 前端通过 cookie 或 localStorage 持有 token

### 安全要求

| 编号 | 规则 |
|------|------|
| AUTH-01 | 后端接口不能只靠前端隐藏，必须有后端校验 |
| AUTH-02 | 会员权益验证必须在后端完成 |
| AUTH-03 | 报告生成权限必须在后端校验 |
| AUTH-04 | 支付订单创建必须在后端完成 |
| AUTH-05 | 分享 token 必须有有效期 |

### 高风险路由（修改需人工复查）

- `backend/app/routes/session.py` — 会话管理
- `backend/app/routes/order.py` — 支付订单
- `backend/app/routes/membership.py` — 会员权益
- `backend/app/services/membership_service.py` — 会员判断
- `backend/app/services/report_permission_service.py` — 报告权限

---

## 四、数据库安全

| 编号 | 规则 |
|------|------|
| DB-01 | 不允许提交真实数据库文件到 Git |
| DB-02 | 数据库写操作必须谨慎，先确认影响范围 |
| DB-03 | 不允许在代码中拼接 SQL（使用 SQLAlchemy ORM） |
| DB-04 | 不允许把真实用户数据用于测试 |
| DB-05 | 数据库迁移脚本必须可回滚 |

---

## 五、依赖安全

| 编号 | 规则 |
|------|------|
| DEP-01 | 新增依赖必须说明来源和必要性 |
| DEP-02 | 不允许引入已知有安全漏洞的依赖版本 |
| DEP-03 | 不允许引入未经验证的 npm/pip 包 |
| DEP-04 | 前端依赖通过 `package.json` 管理 |
| DEP-05 | 后端依赖通过 `requirements.txt` 管理 |

---

## 六、数据保护

| 编号 | 规则 |
|------|------|
| DATA-01 | 不允许把真实用户数据放进测试 |
| DATA-02 | 不允许把用户数据输出到日志 |
| DATA-03 | 用户分数、偏好、报告内容属于隐私数据 |
| DATA-04 | API 响应不应包含数据库内部 ID（使用 UUID） |
| DATA-05 | 不允许 Agent 自行处理线上生产数据 |

---

## 七、部署安全

| 编号 | 规则 |
|------|------|
| DEP-01 | 真实部署配置不进入 Git |
| DEP-02 | 服务器 IP 不硬编码在代码中 |
| DEP-03 | HTTPS 证书路径不暴露 |
| DEP-04 | Nginx 配置使用模板（`deploy/nginx/*.example.conf`） |
| DEP-05 | 不允许直接把 AI 生成代码上线 |

---

## 八、安全变更流程

涉及以下内容的变更必须**单独 PR、人工复查**：

1. 登录/认证逻辑
2. 支付/订单逻辑
3. 会员权益判断
4. 报告权限控制
5. 数据库模型变更
6. 新增依赖
7. API 密钥处理方式变更
8. CORS 配置变更
9. 部署配置变更

---

## 九、安全事件响应

如果发现安全问题（密钥泄露、未授权访问等）：

1. **立即停止**当前任务
2. **报告**安全问题详情
3. **不要尝试自己修复**安全漏洞
4. **等待人工处理**

---

## 十、历史密钥事件处理原则

1. 发现硬编码 key 后必须停止业务开发；
2. 必须先移除当前 HEAD 中的 key；
3. 如果 key 进入 Git 历史，推送远程前必须清理历史（使用 `git-filter-repo`）；
4. 即使历史清理成功，也必须轮换 key；
5. 不允许在报告、日志、对话中展示 key 原文；
6. 清理完成后必须运行 `check-no-secrets`、`check-forbidden-files` 和全历史 grep；
7. 确认所有检查通过后才能推送远程。
