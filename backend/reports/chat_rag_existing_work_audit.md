# Chat + RAG 现有实现自查报告

> 生成时间：2026-06-19
> 任务文档：`agent_files/ZENPATH AI 问答界面重构计划.docx`

---

## 1. 当前 Chat 前端

| 文件 | 存在 | 大小 | 职责 |
|------|------|------|------|
| `frontend/src/pages/Chat.tsx` | ✅ | 11.5KB | 聊天页面：空状态、消息气泡、输入框、sources、answerable 提示 |
| `frontend/src/hooks/useChat.ts` | ✅ | 2.4KB | 调 POST /api/rag/chat/ask，20s 超时，AbortController |
| `frontend/src/components/chat/` | ❌ 不存在 | — | 无聊天组件目录 |
| `frontend/src/store/` | ❌ 不存在 | — | 无全局状态管理 |
| `frontend/src/services/chat/` | ❌ 不存在 | — | 无 chat service 目录 |

**结论：Chat 页面存在且已接通后端 API，但无独立组件目录、无全局 store。**

---

## 2. 当前 Chat 后端接口

| 端点 | 存在 | 职责 |
|------|------|------|
| `POST /api/rag/chat/ask` | ✅ | 简单 RAG 检索 → evidence pack → 返回 answer |
| `POST /api/v1/ai/chat/ask` | ✅ | 旧推荐上下文聊天（用 gaokao.db SQL retriever） |

**结论：有 2 个 chat 端点，但都是简单问答，无会话管理、无历史、无缓存。**

---

## 3. 当前 Chat 能力矩阵

| 能力 | 状态 | 说明 |
|------|------|------|
| 接 RAG | ✅ | ChsiVectorRetriever (FAISS 57K chunks) |
| 接 LLM | ❌ | `/api/rag/chat/ask` 只是返回 RAG evidence 拼接文本，没有真正调用 LLM |
| Streaming | ❌ | 无 |
| 历史会话 | ❌ | 无 DB 表，无 API |
| 缓存 | ❌ | 无 |
| source 引用 | ⚠️ | 有 sources 字段返回，前端展示 |
| answerable 区分 | ✅ | evidence_packer 正确区分 official_evidence / inferential_guidance |
| 资料不足拒答 | ✅ | 就业率等正确返回 answerable=false |
| 会员权限控制 | ❌ | 无每日次数限制、无深度分析锁定 |

---

## 4. RAG 相关模块现状

| 模块 | 路径 | 状态 | 可复用 |
|------|------|------|--------|
| 向量检索 | `backend/rag/retrieval/chsi_vector_retriever.py` | ✅ | ✅ 直接复用 |
| Evidence 打包 | `backend/rag/evidence_packer.py` | ✅ | ✅ 直接复用 |
| 意图路由 | `backend/rag/intent_router.py` | ✅ | ⚠️ 需扩展（新增 school_compare, major_group_risk 等） |
| Prompt 构建 | `backend/rag/prompt_builder.py` | ✅ | ⚠️ 旧版，需升级 |
| LLM 生成 | `backend/rag/generator.py` | ✅ | ⚠️ 旧版，需整合到新 pipeline |
| 后检查 | `backend/rag/post_check.py` | ✅ | ✅ 可复用 |
| 上下文组装 | `backend/app/services/context_assembler.py` | ✅ | ✅ 可复用 |
| Post checker | `backend/app/services/post_checker.py` | ✅ | ✅ 可复用 |
| Reranker | `backend/app/services/rag_reranker.py` | ❌ | 需新建 |
| Query rewriter | `backend/app/services/query_rewriter.py` | ❌ | 需新建 |
| LLM client | `backend/app/services/llm_client.py` | ❌ | 需新建 |
| 缓存服务 | `backend/app/services/chat_cache_service.py` | ❌ | 需新建 |
| Session 服务 | `backend/app/services/chat_session_service.py` | ❌ | 需新建 |
| Chat 主服务 | `backend/app/services/chat_service.py` | ❌ | 需新建 |

---

## 5. 数据库现状

| 表 | 存在 | 说明 |
|----|------|------|
| chat_sessions | ❌ | 需新建 |
| chat_messages | ❌ | 需新建 |
| chat_response_cache | ❌ | 需新建 |
| chat_feedback | ❌ | 需新建 |
| AIConversation / AIChatMessage | ✅ | 旧表，在 models.py 中，可能可复用 |

---

## 6. 不应重复新增

以下已有实现，禁止重复创建：
- `backend/rag/retrieval/chsi_vector_retriever.py` — 向量检索器
- `backend/rag/evidence_packer.py` — evidence 打包
- `backend/rag/intent_router.py` — 意图路由（需扩展而非替换）
- `backend/app/services/membership_service.py` — 会员服务
- `backend/app/services/context_assembler.py` — 上下文装配
- `frontend/src/components/common/*` — 通用组件

---

## 7. 能力缺失总结

| 缺失 | 优先级 |
|------|--------|
| LLM 真正调用（非简单拼接） | P0 |
| 会话管理（创建/列表/消息） | P0 |
| Query rewrite | P1 |
| Rerank | P1 |
| Prompt builder（整合结构化数据+RAG evidence） | P1 |
| 缓存 | P1 |
| 前端侧边栏 + 会话列表 | P1 |
| 前端消息增强（Markdown、复制、重新生成） | P2 |
| 会员权限控制 Chat | P2 |
| DB 表 | P0 |
