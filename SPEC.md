# 鑫科新能源光伏企业全链路ERP系统 - 技术规格说明书

## 1. 系统概述

**系统定位**：面向光伏企业（投资+EPC一体化、户用+工商业双赛道）的全链路数字化管理平台

**核心痛点解决**：
- 资金算不清 → 老板资金看板（多账户多项目穿透）
- 进度不可控 → 项目施工进度管理
- 电费回收难 → 电费结算专项管理
- 成本不透明 → 单项目成本实时归集

**技术架构**：
- 后端：Python Flask + SQLite（可升级 MySQL）
- 前端：Vue 3 + Element Plus（响应式）
- 部署：Railway / 云服务器

---

## 2. 模块清单

### 2.1 老板资金看板（Dashboard）
- 可用自有资金总额 / 联营方资金 / 账内 / 账外
- 资金趋势图（近6个月）
- 项目垫资排行 TOP10
- 应收应付账龄分析
- 延期标红预警

### 2.2 项目管理系统
- 商机管理（线索→跟进→签约）
- 项目立项（基本信息、装机容量、合作模式）
- 施工进度（WBS工序填报）
- 并网管理（发电户号、并网时间）
- 单项目成本台账（材料/人工/分包/融资成本）
- 项目利润实时核算

### 2.3 电费结算系统
- 电站档案管理（装机、地址、并网时间）
- 月度电费账单生成
- 应收款管理与催收提醒
- 回款记录与核销
- 绿电交易/补贴收入

### 2.4 库存管理系统
- 物料主数据（组件、逆变器、支架等）
- 供应商档案
- 入库/出库管理
- 项目领料与成本归集
- 安全库存预警

### 2.5 运维管理系统
- 电站资产台账
- 实时监控数据接入（待对接）
- 巡检工单管理
- 故障报修闭环

---

## 3. 数据模型

### Project（项目）
```
id, name, owner_name, address, capacity_kw, mode(EPC/EMC/代理),
build_type(阵列式/阳光棚/彩钢/车棚), status(商机/签约/施工/并网/运维),
total_invest, paid_amount, remaining_amount, grid_code, grid_date,
created_at, updated_at
```

### ProjectCost（项目成本）
```
id, project_id, cost_type(材料/人工/分包/融资/其他),
amount, description, record_date, created_at
```

### ElectricityBill（电费账单）
```
id, project_id, bill_month, gen_kwh, grid_price, revenue,
payment_status(待确认/待收款/部分收款/已结清), created_at
```

### PaymentRecord（资金流水）
```
id, project_id, direction(收入/支出), category, amount,
payment_date, description, created_at
```

### Material（物料）
```
id, name, category, unit, unit_price, supplier, stock_qty,
safe_stock, created_at
```

### MaterialFlow（物料出入库）
```
id, material_id, project_id, flow_type(入库/出库),
qty, price, flow_date, created_at
```

---

## 4. API 接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/dashboard/summary | 看板核心指标 |
| GET | /api/dashboard/fund-trend | 资金趋势 |
| GET | /api/projects | 项目列表 |
| POST | /api/projects | 新建项目 |
| GET | /api/projects/:id | 项目详情 |
| PUT | /api/projects/:id | 更新项目 |
| GET | /api/projects/:id/costs | 项目成本明细 |
| POST | /api/projects/:id/costs | 添加成本记录 |
| GET | /api/projects/:id/payments | 项目资金流水 |
| POST | /api/payments | 新增资金记录 |
| GET | /api/electricity-bills | 电费账单列表 |
| POST | /api/electricity-bills | 生成电费账单 |
| PUT | /api/electricity-bills/:id | 更新账单状态 |
| GET | /api/materials | 物料列表 |
| POST | /api/materials | 新增物料 |
| GET | /api/material-flows | 物料流水 |
| POST | /api/material-flows | 物料出入库 |
| GET | /api/wbs/:project_id | 施工WBS进度 |
| POST | /api/wbs/:project_id | 更新WBS节点 |

---

## 5. 页面清单

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录 | / | 简单认证 |
| 老板资金看板 | /dashboard | 核心经营指标 |
| 项目列表 | /projects | 所有项目管理 |
| 项目详情 | /projects/:id | 单项目详情+成本+资金 |
| 电费结算 | /electricity | 电费账单管理 |
| 库存管理 | /inventory | 物料管理 |
| 运维工单 | /maintenance | 巡检/故障管理 |

---

## 6. 开发计划

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| 第一阶段 | 框架+项目列表+老板看板 | 🔴 |
| 第二阶段 | 项目成本+资金流水 | 🔴 |
| 第三阶段 | 电费结算系统 | 🔴 |
| 第四阶段 | 库存物料系统 | 🟡 |
| 第五阶段 | 运维工单系统 | 🟡 |