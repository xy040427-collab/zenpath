# 择境 ZENPATH PDF 报告 AIGC 重建 — 实现报告

> 2026-06-23 | 对应: ZENPATH PDF Report Redesign.docx

## 新增文件

| 文件 | 行数 | 用途 |
|------|------|------|
| `backend/app/services/report_quality_guard.py` | 143 | PDF 生成前质量检查，禁止字段名/JSON/debug |
| `backend/app/services/school_logo_service.py` | 115 | 校徽三级回退（本地SVG→CDN→占位SVG） |
| `backend/app/services/report_prompt_builder.py` | 175 | AI prompt 构建器（系统角色+结构化数据+evidence） |
| `backend/app/services/report_ai_writer.py` | 298 | LLM 调用层（DeepSeek→mimo回退，10-15次调用/报告） |
| `backend/app/services/report_rag_evidence_service.py` | 87 | RAG chunks 查询（按学校名匹配） |

## 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/services/report_builder.py` | v1→v2，新增 `school_deep_dives`、`ai_narratives`、Logo 集成；重命名禁止字段（`matched_majors`→`major_directions`、`high_risk_groups`→`risk_groups`、`priority/title/detail`→`step/heading/description`） |
| `backend/app/services/report_pdf_renderer.py` | `print_background=False`（避免 Playwright JSON 管道溢出），A4 margin 10mm |
| `frontend/src/pages/PdfPreview.tsx` | 上次已改（READY信号 + font等待 + promise.race 8s超时） |

## 已验证功能

### Quality Guard
```python
bad = {'matched_majors': [...], 'high_risk_groups': [...]}
validate_report_json(bad)  # → FAILED: "Forbidden field name 'matched_majors'"
```

### Logo 服务
```python
get_school_logo('南京大学')    # → CDN PNG
get_school_logo('未知学校')    # → Placeholder SVG data URI
get_school_logo('南京邮电大学', 'nanjing-university-of-posts-and-telecommunications')  # → Local SVG (if exists)
```

### Report v2 字段
```
Version: v2
school_deep_dives: 10 items (each with logo_url, ai_analysis skeleton)
ai_narratives: present (placeholder — AIGC writer not yet wired in)
key_candidates[*].logo_url: CDN URLs from Urongda
```

### PDF 生成
- 创建 job → pending → processing → completed (~25s)
- 下载: HTTP 200, Content-Type: application/pdf, 34.7MB
- 内容: 10 页，中文正常渲染（Noto Sans SC 字体）

## 待完成 — P1（需 dyad_engine 前端重构）

这些是下一个阶段的任务：

1. **PdfPreview.tsx 视觉重构** — 去掉卡片化，改为咨询报告风格
   - 章节标题 + 横向指标栏 + 正文解释 + 正式表格 + 风险提示框
   - 页眉页脚统一：择境 ZENPATH | 高考志愿填报分析报告 | 第 X 页
   - 目录编号修复（01-14，不是 010/011）
   - 英文字段名→中文标签映射

2. **AIGC Writer 集成** — 将 `report_ai_writer.py` 接入报告生成流程
   - 在 `_save_jiangsu_report()` 后启动异步 enrichment task
   - 或在 PDF 生成前触发（懒加载模式）
   - 需要 DeepSeek API key 在环境变量中

3. **篇幅扩展** — v2 报告有 109 所推荐院校（64冲/24稳/21保），PDF 只显示 10 页
   - 可能需要增加每校详细解析页

## 当前不足

- AIGC 内容仍为空（ai_narratives 和 school_deep_dives[*].ai_analysis 都是空字符串）
- PDF 视觉仍是旧风格（卡片化），dyad_engine 重构待做
- 目录编号格式不对
- 有原始英文字段名（major_directions）直接渲染
