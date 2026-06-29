# Chat RAG 重构验收报告

> 生成时间：2026-06-19
> 任务文档：`agent_files/ZENPATH AI 问答界面重构计划.docx`

---

## 1. 自查报告路径

`backend/reports/chat_rag_existing_work_audit.md`

## 2. 复用的已有文件

| 文件 | 复用方式 |
|------|----------|
| `backend/rag/retrieval/chsi_vector_retriever.py` | 直接复用 FAISS 检索 |
| `backend/rag/evidence_packer.py` | 直接复用 evidence 打包 |
| `backend/rag/intent_router.py` | 通过 retriever.route() 复用 |
| `backend/rag/prompt_builder.py` | 参考设计，新建 `llm_prompt_builder.py` |
| `backend/rag/post_check.py` | 参考设计，新建 `chat_post_checker.py` |
| `backend/app/services/membership_service.py` | 直接复用 |
| `frontend/src/components/common/*` | 直接复用 Button, Badge 等 |

## 3. 新增文件

| 文件 | 职责 |
|------|------|
| `backend/app/services/chat_session_service.py` | 会话/消息/缓存 DB 操作 (chat.db) |
| `backend/app/services/chat_service.py` | 主编排：rewrite → intent → search → rerank → evidence → prompt → LLM → post-check |
| `backend/app/services/chat_cache_service.py` | 缓存 key 生成 + 读写 |
| `backend/app/services/query_rewriter.py` | 模糊指代改写（"这个学校"→"南京大学"） |
| `backend/app/services/rag_reranker.py` | 轻量 rerank（doc_type 优先级 + 匹配加分 + 内容长度） |
| `backend/app/services/llm_prompt_builder.py` | System prompt + 用户背景 + RAG evidence + 推荐上下文 |
| `backend/app/services/llm_client.py` | LLM API 封装 + mock fallback |
| `backend/app/services/chat_post_checker.py` | 回答安全扫描（禁"保证录取"/编造就业率） |
| `backend/app/routes/chat.py` | 6 个 REST API 端点 |

## 4. 修改的后端文件

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | 注册 `chat.router` |

## 5. dyad_engine 前端重构

| 任务 | 步数 | 耗时 |
|------|------|------|
| Chat 完整重构（侧边栏+会话列表+消息流+输入框） | 23 steps | 242s |

**改动文件：**
- `frontend/src/pages/Chat.tsx`：11.5KB → 23.4KB，三栏布局，sidebar + 消息流
- `frontend/src/hooks/useChat.ts`：2.4KB → 6.9KB，完整 session API 管理
- `frontend/src/types/index.ts`：新增 ChatSession 类型

**零 tsc 错误。**

## 6. 新增数据库

`backend/chat.db`（独立于 gaokao.db，避免锁冲突）：
- `chat_sessions` — 会话表（title, province, score, rank, 选科偏好等）
- `chat_messages` — 消息表（role, content, intent, sources, structured_payload）
- `chat_response_cache` — 缓存表（cache_key, answer, sources, expires_at）

## 7. API 列表

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/chat/sessions` | 创建会话 |
| GET | `/api/chat/sessions` | 会话列表 |
| GET | `/api/chat/sessions/{id}` | 会话详情 |
| DELETE | `/api/chat/sessions/{id}` | 删除会话 |
| GET | `/api/chat/sessions/{id}/messages` | 获取消息 |
| POST | `/api/chat/sessions/{id}/messages` | 发送消息（全 pipeline） |

## 8. RAG 检索链路

```
用户问题 → query rewrite → intent route →
  cache check → vector search (top_k=20) →
  rerank (top_k=8) → evidence pack (max 5) →
  prompt build (system + context + evidence) →
  LLM call (DeepSeek v4-pro) → post-check →
  save history + cache → 返回
```

## 9. Rerank 逻辑

`rag_reranker.py`：doc_type 优先级加权 + school/major 命中加分 + content 长度检查 + source_url 存在加分 + intent 专项匹配

## 10. Prompt 模板

`llm_prompt_builder.py`：系统角色 → 用户背景 → 推荐方案上下文 → RAG evidence → 回答边界 → 引用要求 → 免责声明

## 11. 缓存策略

- 公共学校简介：7 天
- 招生章程：7 天
- 个人方案解释：带 context_hash
- Cache key = hash(query + intent + user_context + rag_version)

## 12. 历史会话

- 会话自动标题生成（"江苏 物理 620分 志愿咨询"）
- 消息持久化（含 intent, sources, structured_payload）
- 会话列表按更新时间排序
- 支持归档/删除

## 13. 会员权限

排队待接入（Phase 10 前端 dyad_engine）

## 14. 测试结果

| Query | 结果 |
|-------|------|
| 南京大学学校简介 | ✅ answerable=True, sources=2, Intent=school_profile |
| 南京大学就业率是多少 | ✅ answerable=False, 正确拒答无就业数据 |
| 北京大学招生章程 | ⏳（待跑，pipeline 已通） |

## 15. 当前状态

- 🔵 后端链路完整打通（HTTP 200 验证通过）
- 🔵 前端 dyad 重构完成（Chat.tsx 23KB，三栏布局）
- 🔵 独立 chat.db 避免写锁冲突
- 🟡 前端需要重新 yarn dev / 刷新查看最新 UI
- 🟡 会员权限待接入前端
- 🟡 历史会话删除功能待 dyad_engine UI 完善

## 16. 仍然存在的风险

1. SQLite 同步/异步混用 → 已通过独立 chat.db 解决
2. LLM API 依赖 → mock fallback 已实现
3. FAISS 加载慢（首次 10-30s） → 已通过模块级 lazy load 缓解
