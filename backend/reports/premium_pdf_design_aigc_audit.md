# 择境 ZENPATH PDF 报告 AIGC 重建自查报告

> 2026-06-23 | 对应文档: ZENPATH PDF Report Redesign.docx

## 现有实现状态

| 模块 | 状态 | 大小 | 评估 |
|------|------|------|------|
| `report_builder.py` | ✅ 存在 | 16,953B | 仅构建基础字段，缺少 ai_narratives/school_deep_dives |
| `report_ai_writer.py` | ❌ 不存在 | — | 需新建 |
| `report_prompt_builder.py` | ❌ 不存在 | — | 需新建 |
| `report_rag_evidence_service.py` | ❌ 不存在 | — | 需新建 |
| `school_logo_service.py` | ❌ 不存在 | — | 需新建 |
| `report_quality_guard.py` | ❌ 不存在 | — | 需新建 |
| `PdfPreview.tsx` | ✅ 存在 | 35,666B | 卡片化严重，需 dyad_engine 重构 |
| `Report.tsx` | ✅ 存在 | 36,826B | 摘要页，暂时可接受 |

## 数据源分析

| 数据 | 来源 | 状态 |
|------|------|------|
| 学校 logo | `schools.logo_slug` → `public/logos/{slug}.svg` | ✅ 111 SVG |
| RAG 资料 | `rag_chunks` 表，按 school_name 查 | ✅ 65K+ chunks |
| 推荐数据 | `recommendation_data` (含 rush/stable/safe) | ✅ |
| 专业组 | `jiangsu_group_majors` / `jiangsu_group_plan` | ✅ |
| 趋势 | `jiangsu_group_trends` | ✅ |

## 新增文件清单

| 文件 | 用途 |
|------|------|
| `report_quality_guard.py` | PDF 生成前检查，禁止字段名/JSON/debug |
| `school_logo_service.py` | logo_url 获取 + 占位徽章生成 |
| `report_prompt_builder.py` | 构建 AI prompt（系统角色+结构化数据+evidence） |
| `report_ai_writer.py` | 调用 LLM 生成 AI 解析文案 |
| `report_rag_evidence_service.py` | 按学校名查 RAG chunks |
| 修改: `report_builder.py` | 扩展 ai_narratives 和 school_deep_dives |
| 修改: `PdfPreview.tsx` | 视觉重构（dyad_engine） |
