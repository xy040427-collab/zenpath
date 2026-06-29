# 择境 ZENPATH 报告系统已有实现自查报告

> 生成时间：2026-06-23 14:35  
> 文档对应：ZENPATH Report System.docx 第四节自查要求

---

## 1. 当前 PDF job 创建接口在哪里

**路径**: `backend/app/routes/report.py:414`

```python
@router.post("/{report_id}/pdf/jobs")
async def create_report_pdf_job(...)
```

POST `/api/v1/reports/{report_id}/pdf/jobs`

工作正常，创建 job 并返回 `{success, job_id, status}`。

---

## 2. 当前 job 为什么会一直 pending

**根因**: `backend/app/services/report_pdf_service.py:25` 的 `create_pdf_job()` 只执行以下操作：

1. 验证 report 存在
2. 检查是否有 pending/processing 的已有 job（有则复用）
3. 创建新 `ReportPdfJob(status=pending)` 并 commit

**没有**任何启动后台生成任务、调用 Playwright、或异步处理 PDF 生成的代码。

`report_pdf_renderer.py` **不存在**，所以 PDF 永远无法生成，job 永远停留在 `pending` 状态。

---

## 3. 当前前端如何创建 job、如何轮询

**创建**: `frontend/src/pages/Report.tsx:137` + `frontend/src/services/reportService.ts:170`

```typescript
createPdfJob(reportId, planType) → POST /api/v1/reports/{report_id}/pdf/jobs
```

**轮询**: `Report.tsx:144-159`

```typescript
poll(jobId) → fetchPdfJobStatus(jobId) → GET /api/v1/reports/pdf/jobs/{job_id}
// 每 1500ms 轮询
// 等待 status === 'completed' 或 'failed'
// 无超时保护
```

**问题**: 无超时保护，如果 job 永远 pending，前端永远转圈。

---

## 4. 当前是否已有 PDF 下载接口

**路径**: `backend/app/routes/report.py:458`

`GET /api/v1/reports/{report_id}/pdf/download`

存在，但返回的是 **JSON**（包含 `download_url`），不是真实 PDF 文件流。需要改为 `FileResponse`。

---

## 5. 当前是否已有 report_json

`reports` 表有 `report_data` (JSON) 列，数据由 `backend/app/services/report_builder.py:build_report_json()` 构建。报告数据包含：学生信息、冲稳保结构、候选学校列表等。

当前数据库有 5 条真实报告（均为 `premium` 计划，`ready` 状态）。

---

## 6. 当前是否已有网页报告页

**路径**: `frontend/src/pages/Report.tsx` (795 行)

路由 `/report/:reportId`，展示内容：
- 核心结论
- 考生档案
- 冲稳保结构
- 重点院校预览
- PDF 下载按钮（目前有 pending 问题）

渲染质量：中等，需要向"高级商业摘要页"升级。

---

## 7. 当前是否已有 PDF 预览页

**路径**: `frontend/src/pages/PdfPreview.tsx` (706 行)

路由 `/report/pdf-preview/:reportId`

包含 16 个章节渲染函数（封面、目录、执行摘要…），但：
- 未使用 `.pdf-page` A4 容器
- 未设置 `window.__ZENPATH_PDF_READY__` 信号
- 非 A4 布局（是长滚动页面）

---

## 8. 当前 Playwright / Chromium 是否可用

| 项目 | 状态 |
|------|------|
| Playwright Python | ✅ 1.60.0 |
| Chromium | ✅ chromium-1223 (chrome-linux64) |
| `playwright.sync_api` | ✅ 导入正常 |

---

## 9. 本次准备复用哪些文件

| 文件 | 复用方式 |
|------|----------|
| `backend/app/routes/report.py` | 修改：下载接口返回 FileResponse |
| `backend/app/services/report_pdf_service.py` | 修改：启动后台生成任务 |
| `backend/app/models/models.py` | 不动：表结构已完善 |
| `backend/app/core/database.py` | 不动 |
| `backend/app/services/report_builder.py` | 不动：报告数据构建正常 |
| `frontend/src/pages/Report.tsx` | dyad_engine 修改：超时保护 |
| `frontend/src/pages/PdfPreview.tsx` | dyad_engine 修改：A4 布局 |
| `frontend/src/services/reportService.ts` | 不动：API 调用正常 |
| `backend/gaokao.db` | 不动：表和已有数据正常 |

---

## 10. 本次准备新增/修改哪些文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/report_pdf_renderer.py` | **新建** | Playwright 打开 PdfPreview 页 → 生成真实 PDF |
| `backend/app/services/report_pdf_service.py` | **修改** | `create_pdf_job()` 后启动后台 asyncio task |
| `backend/app/routes/report.py` | **修改** | 下载接口返回 `FileResponse` |
| `frontend/src/pages/PdfPreview.tsx` | **修改** | A4 `.pdf-page` 容器 + `__ZENPATH_PDF_READY__` 信号 |
| `frontend/src/pages/Report.tsx` | **修改** | 轮询超时保护 + 重试按钮 |
