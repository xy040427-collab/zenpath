# RAG 现有工作自查报告

> 生成时间：2026-06-19
> 任务文档：`agent_files/task/CHSI RAG Integration Plan.docx`

---

## 1. 当前项目已有 RAG 相关文件列表

### API 层
| 文件 | 存在 | 大小 | 职责 |
|------|------|------|------|
| `backend/app/api/chsi_rag.py` | ✓ | 1,988 B | FastAPI router：GET /search + POST /evidence |
| `backend/app/api/school_detail.py` | ✓ | 1,271 B | 院校详情 API：GET /{school_name} + /status |

### Service 层
| 文件 | 存在 | 大小 | 职责 |
|------|------|------|------|
| `backend/app/services/rag_retriever.py` | ✓ | 730 B | ChsiRagService 薄封装 |
| `backend/app/services/school_detail_generator.py` | ✓ | 10,483 B | 院校详情生成器：RAG → DeepSeek → 缓存 |
| `backend/app/services/school_info.py` | ✓ | — | 引用 RAG（需进一步确认） |
| `backend/app/services/context_assembler.py` | ✓ | — | 引用 RAG evidence |
| `backend/app/services/recommendation_context.py` | ✓ | — | 引用 RAG |

### RAG 核心库 (`backend/rag/`)
| 文件 | 存在 | 职责 |
|------|------|------|
| `retrieval/chsi_vector_retriever.py` | ✓ | FAISS 向量检索器（57,083 chunks） |
| `evidence_packer.py` | ✓ | 证据打包 + answer_mode 检测 |
| `intent_router.py` | ✓ | 意图路由（school_profile / employment_query） |
| `pipeline.py` | ✓ (65KB) | 主 pipeline |
| `chunker.py` | ✓ | 文档分块 |
| `generator.py` | ✓ | 生成逻辑 |
| `indexer.py` | ✓ | 索引构建 |
| `quality.py` | ✓ (17KB) | 质量控制 |
| `audit.py` | ✓ (13KB) | 审计 |
| `evaluation/evaluate_chsi_rag.py` | ✓ | 检索质量评估（15 queries） |
| `evaluation/validate_chsi_metadata.py` | ✓ | 元数据完整性校验 |
| `indexing/build_chsi_vector_store.py` | ✓ | FAISS 向量库构建脚本 |

### 前端
| 文件 | 存在 | RAG 引用 | 职责 |
|------|------|----------|------|
| `frontend/src/pages/UniversityDetail.tsx` | ✓ (29KB) | chsi ✅ | 院校详情页，调用 /api/chsi/school/ |
| `frontend/src/pages/JiangsuResults.tsx` | ✓ (26KB) | ❌ | 江苏推荐结果页，无 RAG |
| `frontend/src/pages/Report.tsx` | ✓ (10KB) | ❌ | 报告页，无 RAG |
| `frontend/src/pages/Chat.tsx` | ✓ (8KB) | ❌ | Chat 页，无 RAG |
| `frontend/src/pages/Preview.tsx` | ✓ | rag ✅ | 推荐预览页，有 rag_summary 引用 |
| `frontend/src/services/chsiSchool.ts` | ✓ (1,391 B) | chsi ✅ | CHSI 院校详情 service |
| `frontend/src/config/membershipPlans.ts` | ✓ (6KB) | ❌ | 会员配置，无 RAG 字段 |

### 路由层（routes/）
| 文件 | RAG 引用 | 状态 |
|------|----------|------|
| `routes/gaokao_recommend.py` | 提及 rag | 需查是否返回 rag_evidence |
| `routes/chat_context.py` | 提及 rag | 需查 RAG 接入深度 |
| `routes/jiangsu_recommend.py` | ❌ 无 | **未返回 rag_evidence** |

---

## 2. 已注册的 RAG 路由

### GET /api/rag/chsi/search
- **注册状态**：✓ 已注册（`main.py` L41-42）
- **前缀**：`/api/rag/chsi`
- **参数**：`query: str (REQUIRED)`, `top_k: int = 5`, `school_name`, `major_name`, `doc_type`, `scope`, `year` (all optional)
- **方法**：GET
- **返回**：`{success, query, intent, filters, results[], missing_data, warnings}`

### POST /api/rag/chsi/evidence
- **注册状态**：✓ 已注册
- **方法**：POST（JSON body）
- **返回**：evidence 打包结果

### GET /api/chsi/school/{school_name}
- **注册状态**：✓ 已注册
- **方法**：GET
- **功能**：RAG 检索 → DeepSeek AI → 结构化院校详情

### GET /api/chsi/school/{school_name}/status
- **注册状态**：✓ 已注册
- **功能**：缓存状态查询

---

## 3. /api/rag/chsi/search 422 根因

### 根因确认
`query` 参数声明为 `query: str`（无默认值 = REQUIRED）。FastAPI 在缺失该参数时返回 **422 Validation Error**：`{"detail":[{"type":"missing","loc":["query","query"],"msg":"Field required"}]}`。

### 具体触发场景
| 场景 | HTTP 码 |
|------|---------|
| `?query=%E5%8D%97...&top_k=5`（正确编码） | 200 ✓ |
| `?query=&top_k=5`（空字符串） | 200 ✓ |
| `?top_k=5`（缺 query） | 422 |
| 裸中文未编码 | 400（uvicorn HTTP 层） |

### 结论
端点逻辑无 bug。422 仅因 `query` 参数完全缺失触发。不是 Pydantic schema 问题，是 FastAPI 标准参数校验行为。前端不调此端点（直接调 `/api/chsi/school/`）。

---

## 4. RAG 实际数据源

### 当前实际加载
`ChsiVectorRetriever` 从 `rag_output/chsi/export/vector_store/faiss/` 加载：
- `index.faiss`：116.9 MB（FAISS IndexFlatIP，512-dim）
- `docstore.jsonl`：125.6 MB（57,083 条 chunk 完整数据）
- `id_map.json`：1.2 MB
- Embedding model：`BAAI/bge-small-zh-v1.5`
- **实际可检索 chunk 数：57,083**

### 独立 RAG 库
`rag_output/chsi/export/zenpath_chsi_rag.sqlite`：1.49 GB
- `rag_chunks` 表：**65,390 条**（比向量库多 ~8,300 条）
- `schools`：2,950 所
- `school_profiles`：11,321 条
- `admission_policies`：2,887 条
- `major_catalog`：875 条

### 主库 gaokao.db
`backend/gaokao.db` 内 `rag_chunks` 表：约 2,164 条（旧数据，68.9% 无效）

### 结论
✅ **向量库已正确读取 57,083 chunks**，未误读 gaokao.db 的 2,164 条。  
⚠️ SQLite 库多出 8,300 条未入向量库——可能由于质量过滤（is_valid_for_rag=0 被排除）。

---

## 5. 各子系统 RAG 接入状态

| 子系统 | 接入状态 | 说明 |
|--------|----------|------|
| 院校详情页 | ✅ 已接入 | UniversityDetail → /api/chsi/school/ → DeepSeek AI 生成 |
| 推荐结果 (jiangsu) | ❌ 未接入 | 无 rag_evidence 字段 |
| 推荐结果 (generic) | ⚠️ 部分 | Preview.tsx 有 rag_summary 引用 |
| 报告页 | ❌ 未接入 | report_service.py 无 RAG 引用 |
| Chat | ❌ 未接入 | Chat.tsx 无 RAG 引用 |
| 会员权限 | ❌ 未接入 | membershipPlans.ts 无 RAG 字段 |

---

## 6. 可以复用的已有工作

| 组件 | 可复用性 | 说明 |
|------|----------|------|
| `ChsiVectorRetriever` | ✅ 直接复用 | FAISS 检索 57K chunks，metadata filter 完整 |
| `evidence_packer.py` | ✅ 直接复用 | `pack_evidence()` + `answer_mode` 检测 |
| `intent_router.py` | ✅ 直接复用 | school_profile / employment_query 路由 |
| `school_detail_generator.py` | ✅ 直接复用 | RAG→DeepSeek→缓存 完整链路 |
| `chsi_rag.py` 路由 | ✅ 直接复用 | GET /search + POST /evidence |
| `school_detail.py` 路由 | ✅ 直接复用 | 院校详情 API |
| `UniversityDetail.tsx` | ✅ 已有 | 已展示 CHSI 数据 |

---

## 7. 需要新增/修复的工作

| 优先级 | 子系统 | 需要做 |
|--------|--------|--------|
| P0 | RAG search 接口 | 无需修复（端点正常，422 是标准校验行为） |
| P1 | jiangsu 推荐 | 返回 rag_evidence（每个 candidate 附加 CHSI 资料状态） |
| P2 | 报告页 | 接入 RAG 生成院校画像/章程风险章节 |
| P3 | Chat | 接入 RAG 回答院校/章程类问题 |
| P4 | 会员权限 | 控制 RAG 深度内容访问 |
| P5 | 资料不足拒答 | 就业率等无数据 query 需正确拒答 |

---

## 8. 风险提示

1. FAISS 向量库 57,083 chunks < SQLite 65,390 chunks。8,307 条差异需确认是否因质量过滤被排除（大概率是 is_valid_for_rag=0）
2. 院校详情页 AI 生成依赖 DeepSeek API——key 硬编码在 generator 中，若失效则新学校无法生成
3. 前端 UniversityDetail 已有 CHSI 数据展示，但 Report/Chat/JiangsuResults 均未接入
4. 会员控制字段缺失 RAG 相关权限位
