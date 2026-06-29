# 择境 ZENPATH 分析报告系统 — 开工前自查报告

生成时间：2026-06-21

---

## 1. 当前是否已有报告页？

**有。** `frontend/src/pages/Report.tsx`（465行），但当前实现是：
- 接收 Calculator 页面传来的 location.state（score/rank/province/examType）
- 在客户端直接调用 `getRecommendations()` 获取推荐结果
- 渲染完整的冲稳保列表 + 图表面板
- **不是文档要求的"摘要页"**——当前是完整报告页，缺少服务端 Report JSON 驱动

## 2. 当前是否已有 report API？

**有。** `backend/app/routes/report.py`（221行），4 个端点：
| 端点 | 状态 | 说明 |
|------|------|------|
| `POST /api/v1/reports/generate` | ✅ | 生成报告，写入 reports 表 |
| `GET /api/v1/reports/{report_id}` | ✅ | 获取报告详情 |
| `GET /api/v1/reports/{report_id}/export` | ✅ | 导出（硬编码 pdf 元数据） |
| `POST /api/v1/reports/{report_id}/share` | ✅ | 分享（生成 share token） |

**缺失的端点（文档要求）：**
- `GET /api/v1/reports/{id}/summary` — 摘要数据
- `GET /api/v1/reports/{id}/pdf-data` — PDF 完整数据
- `POST /api/v1/reports/{id}/pdf/jobs` — 创建 PDF 任务
- `GET /api/v1/reports/pdf/jobs/{job_id}` — 查询 PDF 任务
- `GET /api/v1/reports/{id}/pdf/download` — 下载 PDF

## 3. 当前是否已有 report_service？

**有。** `backend/app/services/report_service.py`（241行），功能：
- ✅ `generate_report_data()` — 从推荐结果构建报告 JSON
- ✅ `_build_strategy_summary()` — 策略总结文字
- ✅ `_build_level_distribution()` — 层次分布
- ✅ `_build_province_distribution()` — 省份分布
- ✅ `_build_score_bands()` — 分数段分组
- ✅ `_build_rag_summary()` — RAG 资料摘要

**缺失的 service（文档要求）：**
- ❌ `report_builder.py` — 统一构建 Report JSON（含 score_rank_table、admission_lines、trends 等）
- ❌ `report_permission_service.py` — 会员权限裁剪（free/basic/advanced/premium）
- ❌ `report_pdf_service.py` — PDF 生成任务管理
- ❌ `report_pdf_renderer.py` — PDF 渲染（阶段二）

## 4. 当前是否已有 PDF 导出能力？

**无。** 没有任何 PDF 相关文件。`export` 端点返回硬编码元数据（`file_size_kb: 256, pages: 12`），未实际生成 PDF。

## 5. 当前是否已有报告相关数据库表？

**部分有。** 当前 `reports` 表：
```sql
CREATE TABLE reports (
  id VARCHAR(24) PRIMARY KEY,
  application_id VARCHAR(24) NOT NULL,
  recommendation_result_id VARCHAR(24) NOT NULL,
  plan_code VARCHAR(16) NOT NULL,
  status VARCHAR(16),
  report_data JSON,
  pdf_path VARCHAR(256),
  created_at DATETIME,
  completed_at DATETIME
);
```

**与文档 schema 差异：**
- 文档用 `TEXT PRIMARY KEY`，当前用 `VARCHAR(24)`
- 文档有 `user_id`、`province`、`subject_type`、`score`、`rank`、`title`、`summary`、`report_json`——当前缺少这些字段
- 当前有 `application_id` FK + `recommendation_result_id`——文档没有
- **需要扩展现有表**，而非新建

**缺失的表：**
- ❌ `report_pdf_jobs` — PDF 生成任务
- ❌ `report_files` — 文件记录

## 6. 当前是否已有会员权限裁剪？

**无。** 无 `report_permission_service.py`。report route 引用了 pricing plans 但未做权限裁剪。

## 7. 当前哪些文件可复用？

| 文件 | 复用程度 | 说明 |
|------|---------|------|
| `backend/app/routes/report.py` | ⭐⭐⭐ 高 | 基础 CRUD 可复用，需扩展 5 个新端点 |
| `backend/app/services/report_service.py` | ⭐⭐⭐ 高 | 核心构建逻辑可复用，需增强 |
| `backend/app/models/models.py` | ⭐⭐ 中 | `Report` 模型已存在，需扩展字段 |
| `frontend/src/pages/Report.tsx` | ⭐ 低 | 需完全重写为摘要页（文档要求 dyad engine） |
| `frontend/src/hooks/useReport.ts` | ⭐ 低 | 需改为调用 report API |
| `gaokao.db` | ⭐⭐⭐ 高 | 已有 reports 表，扩展即可 |

## 8. 当前哪些能力缺失？

1. ❌ 统一 Report JSON Schema（`report_builder.py`）
2. ❌ 会员权限裁剪（`report_permission_service.py`）
3. ❌ PDF 生成管线（`report_pdf_service.py` + `report_pdf_renderer.py`）
4. ❌ `report_pdf_jobs` + `report_files` 数据库表
5. ❌ 5 个新 API 端点（summary/pdf-data/pdf-jobs/pdf-download）
6. ❌ 网页摘要页（`/report/:reportId`）
7. ❌ PDF 预览页（`/report/pdf-preview/:reportId`）
8. ❌ 前端 report service（调用报告 API）

## 9. 本次计划新增/修改的文件

### 后端（手写）
| 操作 | 文件 | 
|------|------|
| 修改 | `backend/app/routes/report.py` — 扩展 5 个新端点 |
| 修改 | `backend/app/services/report_service.py` — 增强数据构建 |
| 新增 | `backend/app/services/report_builder.py` — 统一 Report JSON |
| 新增 | `backend/app/services/report_permission_service.py` — 权限裁剪 |
| 新增 | `backend/app/services/report_pdf_service.py` — PDF 任务 |
| 修改 | `backend/app/models/models.py` — 扩展 Report 模型 + 新增 PDF 表 |
| 新增 | `backend/migrations/add_report_fields.sql` — 数据库迁移 |

### 前端（dyad engine）
| 操作 | 文件 |
|------|------|
| 重写 | `frontend/src/pages/Report.tsx` — 改为摘要页 |
| 新增 | `frontend/src/pages/PdfPreview.tsx` — PDF 预览页 |
| 新增 | `frontend/src/services/reportService.ts` — 报告 API 调用 |

---

## 自查结论

**现有基础良好，无需从零开始。** 重点在：
1. 扩展现有 reports 表 + 新增 PDF 相关表
2. 扩展 report route（+5 个端点）
3. 新增 3 个 service（builder / permission / pdf）
4. 前端通过 dyad engine 重写 Report.tsx + 新增 PdfPreview.tsx
5. 会员权限裁剪贯穿全链路
