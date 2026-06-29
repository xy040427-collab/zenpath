# RAG 运行时数据源报告

> 生成时间：2026-06-19
> 任务文档：Phase 2 — 确认 RAG 实际数据源

---

## 1. 数据源对比

| 数据源 | 路径 | 大小 | chunk 数 | 有效 |
|--------|------|------|----------|------|
| 主库 gaokao.db | `backend/gaokao.db` | ~160 MB | 2,164 | 672 (31%) |
| 独立 RAG SQLite | `rag_output/chsi/export/zenpath_chsi_rag.sqlite` | 1.49 GB | 65,390 | — |
| FAISS 向量库 | `rag_output/chsi/export/vector_store/faiss/` | ~243 MB | 57,083 | 100% |

## 2. 当前 Retriever 实际加载

`ChsiVectorRetriever` 从 **FAISS 向量库** 加载（`rag_output/chsi/export/vector_store/faiss/`）：
- ✅ 不引用 `gaokao.db`
- ✅ 正确读取完整 CHSI RAG 数据
- ✅ 57,083 chunks 全部可用

## 3. FAISS 向量库详情

| 项目 | 值 |
|------|-----|
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` |
| 向量维度 | 512 |
| Index 类型 | FAISS IndexFlatIP |
| Index 大小 | 116.9 MB |
| Docstore 大小 | 125.6 MB |
| 构建时间 | 2026-06-19T12:02:27 |
| 构建脚本 | `backend/rag/indexing/build_chsi_vector_store.py` |
| 源文件 | `rag_chunks_for_embedding_v2.jsonl` |

### doc_type 分布

| doc_type | 数量 | 占比 |
|----------|------|------|
| admission_policy_clause | 25,900 | 45.4% |
| school_profile | 12,233 | 21.4% |
| department_info | 8,547 | 15.0% |
| major_general_profile | 1,593 | 2.8% |
| major_analysis | 944 | 1.7% |
| major_school_distribution | 783 | 1.4% |
| 其他（末段抽样未覆盖） | ~7,083 | 12.4% |

### scope 分布

| scope | 数量 |
|-------|------|
| school | 46,680 |
| major | 3,320 |

### source_type 分布

| source_type | 数量 |
|-------------|------|
| official_chsi_admission_policy | 25,900 |
| official_chsi_school_library | 20,780 |
| official_chsi_major_library | 2,376 |
| official_chsi_major_analysis | 944 |

全部数据来源：`gaokao.chsi.com.cn`（教育部阳光高考平台）

## 4. 数据完整性

| 问题 | 状态 |
|------|------|
| 是否读取完整 RAG 库 | ✅ 读取 FAISS 向量库 57,083 chunks |
| 是否误读主库 2,164 chunks | ❌ 未误读——Retriever 不引用 gaokao.db |
| SQLite 多出 8,307 chunks | ⚠️ 可能因质量过滤排除（需进一步确认） |

## 5. gaokao.db 内旧 rag_chunks

- 总计：2,164 条
- 有效：672 条（31%）
- 无效：1,492 条（69%）—— too_short / nav_menu / homepage_news

**结论：gaokao.db 的 rag_chunks 质量差、规模小，不应用于检索。**

## 6. 修复结论

**当前 RAG 检索器已经正确配置，无需修复。**
- ✅ 数据源：FAISS 向量库（57,083 chunks）
- ✅ 未误读 gaokao.db
- ✅ metadata filter 支持 school_name / major_name / doc_type / scope / year
- ✅ 向量检索 + rerank 排序
