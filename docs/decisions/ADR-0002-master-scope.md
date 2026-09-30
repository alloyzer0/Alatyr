# ADR-0002：master 分支基线与第一版框架范围

- 状态：Accepted for M0
- 日期：2026-10-01
- 范围：仓库主分支内容、M0 基线和 M1 目标

## 背景

Alatyr 可能应用于普通应用、游戏编辑器、物理模拟和资源工具。现在没有理由让任一领域决定整个框架的对象模型。master 如果过早加入场景树、渲染、物理、完整 ECS 或编辑器 UI，就会从通用基线变成某个领域的集成分支。

## 决策

### 当前 master：M0

`master` 当前包含：

- 语言无关的 Core、Data、Schema、Persistence 协议；
- 术语、模块依赖和架构边界；
- 身份、引用、生命周期、错误和迁移不变量；
- 测试场景、协议向量和基准定义；
- ADR、研究分支规则和领域示例约定。

当前不包含具体语言的生产实现，也不包含完整领域功能。

### 第一版可运行框架：M1

语言选型之后，M1 只实现：

```text
Core         ObjectHandle / PersistentId / TypeId / 生命周期 / 错误
Data         ComponentStore / PropertyStore / Query / Access
Schema       TypeDesc / FieldDesc / 版本 / 默认值 / 约束
Persistence  一种 round-trip 格式 / 引用 / 未知类型 / 简单迁移
```

Tools 和 Adapters 只提供契约、测试夹具和最小示例，不实现完整产品。

## 不进入 M0/M1

- 渲染、物理求解器、网络复制和多人编辑；
- 场景树、Prefab、完整 ECS 或 Archetype 定案；
- 编辑器 UI、资源导入管线、完整 Undo/Redo；
- 脚本语言、代码热重载和插件 ABI；
- 并发模型的最终承诺；
- 生产级文件格式兼容承诺；
- 具体语言、内存布局和所有权实现策略；
- 领域专用的 Transform、Node、Actor、RigidBody 和 Scene 语义。

这些内容可以在 `research/*` 或 `examples/<domain>` 中验证，只有沉淀为跨领域协议后才考虑回收。

## M1 验收

M1 必须通过对象删除、旧句柄失效、跨文件引用、未知类型保留、schema 迁移、损坏数据报告和组件未挂载内存成本等测试。至少两个领域示例必须能在不改变 Core 语义的情况下接入。

## 后续变更

任何扩大 master 范围的变更都需要新的 ADR，并说明跨领域收益、成本、失败语义、测试证据，以及为什么不应放在 Adapter 或研究分支。
