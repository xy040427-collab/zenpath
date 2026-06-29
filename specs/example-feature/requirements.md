# Spec: [功能名称]

> 状态：Draft | In Review | Approved | Implemented | Verified
> 创建日期：YYYY-MM-DD
> 最后更新：YYYY-MM-DD
> 负责人：[姓名]

---

## 1. 背景

[为什么需要这个功能？解决什么问题？]

## 2. 用户故事

```
作为 [角色]
我希望 [功能描述]
以便 [获得的价值]
```

## 3. 必须实现

- [ ] 核心功能点 1
- [ ] 核心功能点 2
- [ ] 核心功能点 3

## 4. 不做什么（Out of Scope）

- 明确不做的功能 1
- 明确不做的功能 2

## 5. 允许修改范围

| 文件/目录 | 修改类型 | 说明 |
|-----------|---------|------|
| `frontend/src/pages/Xxx.tsx` | 新增/修改 | 页面组件 |
| `frontend/src/components/xxx/` | 新增 | 新组件 |

## 6. 禁止修改范围

| 文件/目录 | 原因 |
|-----------|------|
| `backend/app/models/models.py` | 涉及数据库结构 |
| `backend/app/routes/session.py` | 登录鉴权逻辑 |
| `frontend/tailwind.config.js` | 设计系统 token |
| `.env` | 敏感配置 |

## 7. 验收标准

- [ ] `npm run build` 构建通过，无 error
- [ ] `npm run type-check` 类型检查通过
- [ ] 相关页面可正常打开，无白屏
- [ ] UI 符合设计规范（参见 docs/STYLE_GUIDE.md）
- [ ] 不影响已有页面和功能
- [ ] 无 mock 冒充真实功能
- [ ] 无新增无关依赖

## 8. 风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| [风险描述] | 高/中/低 | [应对方案] |

## 9. 回滚方式

- 通过 Git 分支回滚：`git revert <commit>` 或删除分支
- 如涉及数据库变更，需提供回滚迁移脚本
