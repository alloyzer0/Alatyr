# Alatyr 可复用框架架构草案

- 状态：研究材料，不是主分支架构决议
- 目标：把 Alatyr 设计成可组合的运行时基础设施，而不是跨语言互操作格式
- 适用方向：普通应用、文档系统、编辑器、游戏引擎、物理模拟和其他需要可选对象数据的宿主

## 1. 定位

Alatyr 应统一语义和边界，允许每个能力模块选择自己的布局、分配器、反射实现和执行方式。Rust、Zig、C++ 原型的主要价值是验证这种架构能否以不同成本实现，而不是建立统一 ABI 或要求所有实现共享 wire format。

最小对象不是“带有所有属性的通用对象”，而是一个有身份和生命周期的锚点。组件、属性、关系、资源、Schema、持久化和编辑器状态按能力挂载。

## 2. 三个平面

### Control Plane

负责跨模块必须一致的控制语义：

- `Runtime`、`Scope` 和对象句柄的隔离；
- Type/Capability 注册和冲突检测；
- 创建、销毁、代际失效和生命周期协调；
- 事务边界、修订号和结构化错误；
- 模块的安装、停止和清理通知。

Control Plane 不保存领域数据，也不规定组件使用哪种容器。

### Data Plane

由模块拥有实际数据和索引：

- payload component、marker/tag；
- fixed field 和 dynamic property；
- relation/edge；
- singleton/global data；
- resource/asset 引用和外部状态。

各 Store 自己管理内存、布局、查询索引和分配器，只向 Runtime 暴露身份定位、存在性和生命周期接口。

### Observation / IO Plane

对 Data Plane 提供可选的观察和外部表示：

- Schema、反射、校验和迁移；
- 查询视图和索引；
- Document、Snapshot 和 Persistence；
- 变更事件、Undo/Redo 和 dirty tracking；
- Inspector、网络同步和调试投影。

这些能力不应默认成为每个对象的字段。

## 3. 最小运行时

建议把最低内核限制为：

```text
Runtime / Scope
ObjectHandle(slot, generation)
ObjectType / ComponentType / Capability registry
Lifecycle coordinator
Error context
```

`PersistentId`、Schema、动态属性、事件和序列化都可以是可选能力。`Scope` 可以代表一个文档、编辑器预览世界、物理世界或应用会话；句柄不得跨 Scope 使用。

对象类型和组件类型可以共享一个稳定命名空间，但协议中应显式标注 kind，不能让 `create(type_id)` 和 `attach(component_type)` 的含义依赖实现者猜测。

## 4. Capability 合同

每个可选模块至少声明：

```text
CapabilityDesc {
    id
    version
    scope                 // runtime, type, instance
    requires / provides
    storage_policy
    lifecycle_hooks
    persistence_policy
    cost_contract
}
```

模块安装后可以注册 Store、查询、生命周期钩子或服务。模块停用、卸载或迁移必须说明已有状态是拒绝操作、冻结、迁移、清空还是保留为 opaque 数据。

能力的声明不等于每个实例已经分配数据。模块可以使用按需分配的 side table，但必须订阅对象销毁并完成清理。

## 5. 可选能力的成本契约

“不需要某属性时不占资源”应解释为可验证的 absence-cost 规则：

| 成本范围 | 示例 | 未启用时的要求 |
| --- | --- | --- |
| Runtime | 注册表、服务、模块索引 | 不存在能力项和相关服务 |
| Type | TypeDesc、ComponentStore | 不创建该类型描述和存储 |
| Object | PersistentId、关系、组件值 | 不增加对应实例字段 |
| Operation | 序列化、校验、排序、事件 | 不做隐式扫描和隐式执行 |

允许基础句柄表和模块注册开销，不能要求所有对象携带通用字典、虚函数、锁或类型擦除 Value。能力启用后的成本由对应模块负责并应可观察。

## 6. 推荐组合

```text
Bare              Identity + Lifecycle
Data              Bare + Component/Relation Store + Query
Introspectable    Data + Schema + Validation
Persistable       Data + Document/Snapshot + References
Reactive          Data + Revision + Events
Editor            Data + Schema + Persistence + Relation + Undo
Physics           Data + Resource + Physics Adapter
```

并发、确定性、资源加载、插件 ABI 和网络复制建议作为独立 Profile。领域适配器可以组合多个 Profile，但不应迫使所有宿主启用完整集合。

## 7. 需要继续验证的架构不变量

1. 不同 Scope 的句柄不能互用，Scope 销毁后句柄和订阅全部失效；
2. 创建最小对象只支付基础身份成本，启用能力后才产生相应实例或 Store 成本；
3. 跨多个 Store 的一次变更要么整体提交，要么恢复输入；
4. 变更事件只在提交后发布，并携带 revision；
5. 未知类型、字段或资源经过加载再保存时不会静默丢失；
6. 资源生命周期独立于对象生命周期；
7. transient 对象、克隆 Scope 和预览 Scope 的持久化规则明确；
8. 组件、关系和属性的查询视图在结构变化后的失效规则一致。

这些不变量比统一函数签名、统一 ABI 或继续增加领域 API 更能证明框架具有可复用性。
