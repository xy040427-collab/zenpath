# RAG 择境集成验收报告

> 生成时间：2026-06-19
> 任务文档：`agent_files/task/CHSI RAG Integration Plan.docx`

---

## 1. 自查报告路径

- `backend/reports/rag_existing_work_audit.md` — 第一阶段：现有工作自查
- `backend/reports/rag_runtime_source_report.md` — 第二阶段：数据源确认

---

## 2. 复用的已有文件

| 文件 | 复用方式 |
|------|----------|
| `backend/rag/retrieval/chsi_vector_retriever.py` | 直接复用，仅添加 source_url filter |
| `backend/rag/evidence_packer.py` | 完全复用，无需修改 |
| `backend/rag/intent_router.py` | 完全复用 |
| `backend/app/services/rag_retriever.py` | 作为 ChsiRagService 薄封装复用 |
| `backend/app/services/school_detail_generator.py` | 直接复用 |
| `backend/app/api/chsi_rag.py` | 修复响应格式后复用 |
| `backend/app/api/school_detail.py` | 直接复用 |
| `frontend/src/pages/UniversityDetail.tsx` | 已有 CHSI 数据展示，复用 |
| `frontend/src/services/chsiSchool.ts` | 直接复用 |

---

## 3. 新增/修改的文件

### 新增

| 文件 | 职责 |
|------|------|
| `backend/app/api/rag_chat.py` | CHSI RAG 通用问答端点（POST /api/rag/chat/ask） |
| `backend/reports/rag_existing_work_audit.md` | 自查报告 |
| `backend/reports/rag_runtime_source_report.md` | 数据源报告 |

### 修改

| 文件 | 改动 |
|------|------|
| `backend/app/api/chsi_rag.py` | 响应格式对齐：添加 top_k / major_name 字段，清理输出 |
| `backend/rag/retrieval/chsi_vector_retriever.py` | 添加 source_url 到 metadata filter 白名单 |
| `backend/app/routes/jiangsu_recommend.py` | 添加 rag_evidence 批查（Phase 7），更新 membership_controls |
| `backend/app/services/report_service.py` | 添加 _build_rag_summary 函数 |
| `backend/app/services/membership_service.py` | 四个 RAG 权限字段 |
| `backend/app/main.py` | 注册 rag_chat_router |

---

## 4. 修复的接口

### GET /api/rag/chsi/search
- **状态**：✅ 可用
- **修复内容**：响应格式对齐任务文档要求（top_k, major_name, clean results）
- **422 根因**：query 参数缺失时 FastAPI 标准校验行为，非 bug
- **测试**：6/7 query HIT，就业率正确拒答

### POST /api/rag/chsi/evidence
- **状态**：✅ 正常
- answerable=True → official_evidence 模式
- answerable=False → inferential_guidance 模式（就业率等）

---

## 5. RAG 实际加载

| 项目 | 值 |
|------|-----|
| 路径 | `rag_output/chsi/export/vector_store/faiss/` |
| 索引类型 | FAISS IndexFlatIP |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 |
| 可检索 chunk 数 | 57,083 |
| 覆盖率 | 2,950 所学校 |
| 未误读 gaokao.db | ✅ 验证通过 |

---

## 6. 各子系统接入状态

| 子系统 | 后端 | 前端 |
|--------|------|------|
| 院校详情页 | ✅ /api/chsi/school/ → DeepSeek + RAG | ✅ UniversityDetail.tsx 5 tab 展示 CHSI 数据 |
| 推荐结果 rag_evidence | ✅ jiangsu_recommend 返回 rag_evidence | ⚠️ 需 dyad_engine 添加 UI 指示器 |
| 报告页 RAG 章节 | ✅ report_service 返回 rag_summary | ⚠️ 需 dyad_engine 修改 Report.tsx |
| Chat RAG | ✅ POST /api/rag/chat/ask | ⚠️ useChat.ts mock 需 dyad_engine 重写 |
| 会员 RAG 权限 | ✅ 四个 RAG 字段已添加 | ⚠️ 需 dyad_engine 更新 Pricing/UI |

---

## 7. 测试 query 结果

| Query | 命中 | doc_type | source_url | 编造 | 拒答 |
|-------|------|----------|------------|------|------|
| 南京大学学校简介 | ✅ HIT | school_profile | ✅ | — | — |
| 北京大学招生章程 | ✅ HIT | admission_policy_clause | ✅ | — | — |
| 复旦大学招生章程 | ✅ HIT | admission_policy_clause | ✅ | — | — |
| 计算机专业介绍 | ✅ HIT | major_analysis | ✅ | — | — |
| 临床医学专业介绍 | ✅ HIT | major_general_profile | ✅ | — | — |
| 南京大学就业率是多少 | ✅ CORRECT | — | — | ❌ 未编造 | ✅ 资料不足 |
| 上海交通大学医学院招生章程 | ❌ MISS | — | — | ❌ 未编造 | ✅ 无数据（学校名不匹配） |

---

## 8. 会员权限

| 字段 | free | basic | advanced | premium |
|------|------|-------|----------|---------|
| can_view_rag_school_profile | ✅ | ✅ | ✅ | ✅ |
| can_view_rag_admission_policy | ❌ | ✅ | ✅ | ✅ |
| can_view_rag_deep_analysis | ❌ | ❌ | ✅ | ✅ |
| can_view_rag_report_section | ❌ | ❌ | ✅ | ✅ |

---

## 9. 当前风险

1. **前端 UI 待 dyad_engine**：JiangsuResults / Report / Chat / Pricing 页面的 RAG UI 修改尚未通过 dyad_engine 执行（任务文档硬性要求所有前端修改走 dyad_engine）
2. **上海交通大学医学院**：CHSI docstore 以"上海交通大学"为主名，带"医学院"后缀的查询无法匹配
3. **DeepSeek API 依赖**：院校详情生成依赖 DeepSeek API，网络或配额问题会导致新学校首次访问失败
4. **FAISS 加载延迟**：首次请求加载 240MB 向量库需 10-30 秒

---

## 10. 未接入的数据类型

按任务文档要求，以下数据类型不接入 RAG（继续使用结构化 DB）：
- 一分一段表、投档线、专业组计划数、选科匹配 → 结构化 DB
- 就业率、学科排名 → 正确拒答
- 招生计划变化 → 不参与计算

---

## 11. 下一步

1. 用 dyad_engine 修改 JiangsuResults.tsx：展示 rag_evidence 标记
2. 用 dyad_engine 修改 Report.tsx：展示 RAG 章节
3. 用 dyad_engine 重写 useChat.ts / Chat.tsx：对接 /api/rag/chat/ask
4. 用 dyad_engine 更新 Pricing.tsx：添加 RAG 功能说明

完成后等待验收。
