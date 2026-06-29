# 择境 ZENPATH — 发布与回滚指南

> 本文档定义了代码发布到生产的标准流程。
> 所有发布必须经过验证，不允许直接把 AI 生成代码上线。

---

## 一、发布前检查清单

### 必须通过

- [ ] `cd frontend && npm run build` 构建成功
- [ ] 后端 `uvicorn app.main:app` 启动成功
- [ ] 核心页面无白屏
- [ ] 导航可正常跳转
- [ ] 关键 API 响应正常

### 重点验收页面

| 页面 | 路由 | 验收重点 |
|------|------|---------|
| 首页 | `/` | 加载正常、标题可见 |
| 聊天 | `/chat` | 消息发送、AI 响应 |
| 计算器 | `/calculator` | 分数输入、推荐结果 |
| 定价 | `/pricing` | 套餐显示、按钮可点 |
| 报告 | `/report` | 报告生成、PDF 预览 |
| 大学详情 | `/university/:id` | 数据加载、图表显示 |

### 重点验收功能

| 功能 | 涉及文件 | 验收方式 |
|------|---------|---------|
| 登录/会话 | `routes/session.py` | 创建匿名会话 |
| 推荐引擎 | `services/recommendation_service.py` | 输入分数获取推荐 |
| 报告生成 | `services/report_service.py` | 生成并预览报告 |
| 会员权益 | `services/membership_service.py` | 验证权限判断 |
| 支付 | `routes/order.py` | 订单创建流程 |
| RAG 聊天 | `api/rag_chat.py` | AI 对话功能 |

---

## 二、发布流程

```
1. 功能分支合并到 main
2. 在 main 上运行 build
3. 在 main 上运行页面验收
4. 确认 .env 配置正确
5. 确认数据库 schema 兼容
6. 部署到服务器
7. 验证线上功能
8. 监控日志 15 分钟
```

### 部署命令（参考）

```bash
# 1. 拉取最新代码
cd /home/ubuntu/gaokao-volunteer
git pull origin main

# 2. 前端构建
cd frontend && npm install && npm run build

# 3. 后端依赖
cd ../backend && pip install -r requirements.txt

# 4. 重启后端
pkill -f uvicorn
nohup uvicorn app.main:app --host 0.0.0.0 --port 3458 &

# 5. 重载 Nginx
sudo nginx -s reload
```

---

## 三、禁止事项

| 编号 | 禁止行为 |
|------|---------|
| R-01 | 直接把 AI 生成代码上线，不经 build 验证 |
| R-02 | 跳过页面验收直接部署 |
| R-03 | 不检查 .env 就部署 |
| R-04 | 不备份数据库就做 schema 变更 |
| R-05 | 一次部署多个不相关功能 |
| R-06 | 不监控部署后日志 |

---

## 四、回滚方案

### Git 回滚

```bash
# 回滚到上一个 commit
git revert HEAD
git push origin main

# 回滚到指定 commit
git revert <commit-hash>
git push origin main

# 强制回滚（谨慎使用）
git reset --hard <commit-hash>
git push --force origin main
```

### 前端回滚

```bash
# 重新构建上一个版本
git checkout <previous-commit> -- frontend/
cd frontend && npm run build
sudo nginx -s reload
```

### 后端回滚

```bash
# 回滚后端代码
git checkout <previous-commit> -- backend/

# 重启后端
pkill -f uvicorn
nohup uvicorn app.main:app --host 0.0.0.0 --port 3458 &
```

### 数据库回滚

```bash
# 使用 Alembic 回滚迁移
cd backend
alembic downgrade -1

# 或从备份恢复
cp gaokao.db.backup gaokao.db
```

---

## 五、发布后监控

部署后 15 分钟内检查：

1. **后端日志**：是否有异常 traceback
2. **API 响应**：关键接口是否 200
3. **页面加载**：首页、聊天、计算器是否正常
4. **数据库**：是否有锁定或连接错误
5. **内存/CPU**：是否有异常飙升

---

## 六、紧急回滚触发条件

以下情况必须**立即回滚**：

- 页面白屏
- API 全部 500
- 数据库损坏
- 用户数据泄露
- 支付流程异常
- 服务器资源耗尽

回滚后**立即通知**相关人员。
