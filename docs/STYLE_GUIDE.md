# 择境 ZENPATH — UI 与代码风格规范

> 本文档定义了前端 UI 和代码的风格标准。
> 所有前端修改必须遵循本规范。
> 不允许引入与现有风格冲突的新设计。

---

## 一、技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 框架 | React | 18.2 |
| 语言 | TypeScript | 5.3 |
| 构建 | Vite | 5.0 |
| 样式 | Tailwind CSS | 3.3 |
| 路由 | React Router DOM | 6.20 |
| 动画 | Framer Motion | 10.16 |
| 图标 | Lucide React | 1.17 |
| 图表 | Recharts | 2.10 |
| HTTP | Axios | 1.6 |

---

## 二、品牌色彩

品牌色彩定义在 `frontend/tailwind.config.js`，**不允许随意修改**。

| 色板 | Tailwind 类 | 色值 | 用途 |
|------|------------|------|------|
| 墨绿 | `brand-900` | `#1A2E22` | 主背景、标题 |
| 深绿 | `brand-700` | `#2D4A3E` | 次背景 |
| 中绿 | `brand-500` | `#4A6A5C` | 按钮、强调 |
| 浅绿 | `brand-100` | `#E2ECE6` | 浅背景 |
| 米色 | `beige-100` | `#F5F0E8` | 页面背景 |
| 暖米 | `beige-200` | `#F0EAE0` | 卡片背景 |
| 金色 | `accent-gold` | `#C4A45C` | 高亮、CTA |
| 墨字 | `ink` | `#4A4A4A` | 正文 |
| 灰字 | `ink-muted` | `#8A8A8A` | 辅助文字 |

**禁止**：
- 引入新的色值（如 `#FF6B6B`、`text-red-500`）
- 使用 Tailwind 默认色板中的亮色（如 `text-blue-500`、`bg-green-400`）
- 修改 `tailwind.config.js` 中的任何颜色定义

---

## 三、字体规范

| 用途 | 字体 | Tailwind 类 |
|------|------|------------|
| 标题 | Cormorant Garamond | `font-serif` |
| 正文 | Inter | `font-sans` |
| 代码 | JetBrains Mono | `font-mono` |
| 大写字母标签 | 全大写 + 字距 | `text-caption-mono` |
| 按钮文字 | 全大写 + 字距 | `text-btn` |

字号：
- h1: `text-h1`（3.5rem）
- h2: `text-h2`（2.25rem）
- h3: `text-h3`（1.5rem）
- 正文: 18px
- 小字: 14px

---

## 四、组件使用规范

### 优先使用现有组件

修改 UI 前，先检查 `frontend/src/components/common/`：

| 组件 | 文件 | 用途 |
|------|------|------|
| Button | `Button.tsx` | 统一按钮 |
| Modal | `Modal.tsx` | 弹窗 |
| Toast | `Toast.tsx` | 消息提示 |
| Input | `Input.tsx` | 输入框 |
| Badge | `Badge.tsx` | 标签 |
| EmptyState | `EmptyState.tsx` | 空状态 |
| LoadingSkeleton | `LoadingSkeleton.tsx` | 加载骨架 |
| StepIndicator | `StepIndicator.tsx` | 步骤指示器 |
| PricingCard | `PricingCard.tsx` | 套餐卡片 |
| RecommendationCard | `RecommendationCard.tsx` | 推荐卡片 |
| ScoreBadge | `ScoreBadge.tsx` | 分数标签 |

**禁止**：
- 不看现有组件就新建同类组件
- 创建功能重复的组件
- 在页面中直接写 inline 样式代替组件

### 新建组件规则

如果确实需要新建组件：
1. 先确认现有组件无法满足
2. 放在正确的子目录（`common/`、`charts/`、`panels/`、`school/`）
3. 使用 TypeScript 接口定义 props
4. 遵循现有命名和样式风格
5. 在报告中说明新增了什么组件

---

## 五、页面布局规范

### 整体布局

- 使用 `MainLayout.tsx` 作为页面容器
- 导航栏 `Navbar.tsx` 固定在顶部
- 页脚 `Footer.tsx` 在底部
- 内容区域使用 `max-w-7xl mx-auto` 居中

### 响应式

- 移动端优先
- 使用 Tailwind 响应式前缀：`sm:`、`md:`、`lg:`
- 导航栏在移动端需要折叠菜单
- 卡片在移动端单列，桌面端多列

### 间距

- 页面 padding: `px-4 md:px-8`
- 卡片间距: `gap-6 md:gap-8`
- 区块间距: `py-12 md:py-16`
- 卡片内 padding: `p-6`

---

## 六、交互规范

### 动画

- 使用 Framer Motion，但保持轻量
- 入场动画：`initial={{ opacity: 0, y: 20 }}` + `animate={{ opacity: 1, y: 0 }}`
- 按钮 hover：`whileHover={{ scale: 1.02 }}`
- 页面切换：淡入淡出，时长 300ms
- **禁止**：复杂路径动画、粒子效果、3D 变换

### 按钮

- 主按钮：`bg-brand-500 text-white` + `rounded-btn`
- 次按钮：`border border-brand-500 text-brand-500`
- 文字按钮：`text-brand-500 underline`
- 禁用状态：`opacity-50 cursor-not-allowed`

### 弹窗

- 使用 `Modal.tsx` 组件
- 背景遮罩：`bg-black/50 backdrop-blur-sm`
- 内容区：`bg-white rounded-xl shadow-elevated`
- 关闭方式：点击遮罩 + 右上角 X + Esc 键

### 空状态

- 使用 `EmptyState.tsx` 组件
- 显示图标 + 文字 + 可选操作按钮
- 文字使用 `ink-muted` 色

---

## 七、API 调用规范

- 所有 API 调用集中在 `frontend/src/services/`
- 使用 Axios 实例，baseURL 由 Vite proxy 处理
- 错误处理统一在 service 层
- 类型定义放在 `frontend/src/types/`
- **禁止**：在页面组件中直接写 `axios.get()`

---

## 八、代码风格

### TypeScript

- 优先使用 `interface` 定义对象类型
- 避免 `any`，实在需要时加注释说明原因
- 组件 props 必须定义类型接口
- 使用 `const` 断言或枚举代替魔法字符串

### 文件组织

- 每个页面一个文件，在 `pages/`
- 通用组件在 `components/common/`
- 页面专属组件在 `components/panels/` 或 `components/school/`
- 自定义 Hook 在 `hooks/`
- 工具函数在 `utils/`

### 命名

- 组件文件：PascalCase（`Button.tsx`）
- 工具文件：camelCase（`formatters.ts`）
- 类型文件：camelCase（`index.ts`）
- 常量：UPPER_SNAKE_CASE

---

## 九、绝对禁止

| 编号 | 行为 |
|------|------|
| S-01 | 随机写一套新颜色 |
| S-02 | 创建功能重复的组件 |
| S-03 | 在页面中写 inline 样式 |
| S-04 | 使用 Tailwind 默认亮色 |
| S-05 | 修改 tailwind.config.js |
| S-06 | 引入新的 CSS 框架 |
| S-07 | 使用 !important |
| S-08 | 删除现有组件 |
| S-09 | 不考虑移动端就提交 |
| S-10 | 在组件中直接调 API |
