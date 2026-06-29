# Tasks: [功能名称]

> 关联 Spec: specs/example-feature/requirements.md
> 关联 Design: specs/example-feature/design.md
> 总任务数：N
> 预计总工时：Xh

---

## Task 1: [任务名称]

- **目标**：[具体、可验证的目标]
- **允许修改范围**：
  - `frontend/src/components/xxx/NewComponent.tsx`（新增）
  - `frontend/src/pages/XxxPage.tsx`（修改第 N 行区域）
- **禁止修改范围**：
  - 不得修改其他页面
  - 不得修改后端代码
  - 不得新增 npm 依赖
- **验收标准**：
  - [ ] [具体可检查的条件 1]
  - [ ] [具体可检查的条件 2]
- **建议测试方式**：
  - `npm run build` 无报错
  - 页面打开可见 [具体内容]
- **适合 Agent 执行**：是/否
- **需要人工确认**：是/否
- **预计工时**：Xh

---

## Task 2: [任务名称]

- **目标**：[具体、可验证的目标]
- **允许修改范围**：
  - [文件列表]
- **禁止修改范围**：
  - [文件列表]
- **验收标准**：
  - [ ] [条件]
- **建议测试方式**：
  - [测试命令或检查方式]
- **适合 Agent 执行**：是/否
- **需要人工确认**：是/否
- **预计工时**：Xh

---

## 执行顺序

```
Task 1 → Task 2 → Task 3 → 集成验证
```

## 依赖关系

- Task 2 依赖 Task 1 完成
- Task 3 依赖 Task 2 完成

## 全局验收

所有任务完成后，运行：

```bash
cd frontend && npm run build
cd frontend && npm run type-check
```

确认无报错后，人工检查核心页面。
