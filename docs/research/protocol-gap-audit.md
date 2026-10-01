# Alatyr 协议缺口审计

- 状态：研究材料，不是 M0.1 接受决议
- 范围：审查当前 Core、Data、Schema、Persistence、Extension 在应用程序、编辑器、物理模拟、渲染和插件场景中的互操作缺口
- 目标：先补全跨实现必须一致的语义，再把并发、资源、编辑器和 ABI 能力拆成可选 Profile

当前 M0 的分层方向是正确的，但若直接开始多个语言实现，仍有几处文字可以被不同实现解释成不同协议。最优先的工作不是加入更多领域 API，而是收紧身份、销毁、查询、事务和可选能力的语义。

## P0：进入下一版语言无关协议

### 1. 身份作用域和注册冲突

需要明确：

- `ObjectHandle` 绑定哪个 `Runtime`/`World`，跨实例使用时必须返回什么错误；
- `PersistentId` 的命名空间、唯一性范围、销毁后是否允许复用；
- `TypeId`、`FieldId` 的稳定范围、生成规则和注册冲突；
- 对象的 `TypeId` 是否不可变；`component_type` 是否就是 `TypeId`，还是单独的 `ComponentTypeId`。

这些规则决定不同实现能否交换句柄、Schema 和持久化数据。

### 2. 销毁、强引用和协调边界

当前协议同时出现“strong 保持目标存活”和“显式 destroy 后引用失效”两种可能含义，需要二选一或拆成两个概念：

- `reference`：指向目标，但目标销毁后可以失效；
- `retain/owner`：阻止销毁，直到释放或转入 pending destroy。

还需定义销毁的线性化点、幂等性、延迟销毁、组件/属性/扩展状态清理顺序，以及销毁后旧句柄、查询视图和引用的可见结果。

### 3. Data 操作和查询视图

至少要确定：

- `attach` 已有同类组件时是替换、错误还是幂等；
- `detach`/`get` 缺失组件时的结果；
- 查询返回 live view、snapshot 还是稳定句柄列表；
- 查询期间结构修改、销毁和组件迁移是拒绝、延迟还是使视图失效；
- `Read`、`Write`、`Structural` 等访问模式与 `AccessConflict` 的对应关系；
- 顺序默认未定义时，如何显式请求稳定顺序。

固定字段和动态属性还缺少最小的 `read`、`write`、`patch`、`clear` 语义。若暂不纳入 M0，应明确由 Property/Editor Profile 提供，避免各实现自行发明。

### 4. 事务、修订和变更顺序

创建、销毁、组件变更、字段写入和加载迁移都需要说明是否原子。建议定义最小抽象：

```text
begin -> operations -> commit | rollback
```

并规定对象或文档 `revision` 的递增点、冲突结果和事件发布时机。至少应保证失败不会留下调用方无法观察的半提交状态；事件默认在 commit 后发布，并携带单调的事务序号。

### 5. Persistence 的对象图边界

`PersistentId` 在 Core 中可以缺失，因此 envelope 中应明确 `persistent_id` 是 optional，或规定 transient 对象不可直接序列化。Persistence 还需要区分单对象 envelope 与对象图/文档容器，并定义：

- 根对象、循环引用、重复 ID 和 ID 冲突；
- strong/weak/external 引用的编码和缺失策略；
- 已知类型中的未知字段是否 opaque 保留；
- 加载/迁移的提交、回滚和部分可见性。

### 6. 错误的可互操作语义

现有错误类别还应补充操作结果约束，例如 `AlreadyAttached`、`MissingComponent`、`DuplicateId`、`UnsupportedVersion`、`ValidationFailed`、`ResourceLimit`、`Cancelled`。错误对象至少需要 machine-readable code、诊断位置、严重级别、是否可重试、事务结果和因果链；各语言可以用不同语法实现，但不能静默降级。

### 7. 可选能力的零成本契约

这是 Alatyr 可复用框架的关键缺口。`capabilities` 目前只有元数据，还没有规定能力如何启用及其成本。应定义：

- 能力的归属（Runtime、类型、组件或扩展）；
- 依赖、启用时机和禁用结果；
- 实例级字段、sidecar 存储、索引、扫描和缓存的成本声明；
- 未启用能力时不得增加实例字段、每帧扫描或隐式序列化；
- 能力关闭时已有数据如何保留或拒绝访问。

这样才能验证“没有某属性时不占内存和计算资源”，同时不把具体布局写死。

## P1：以独立 Profile 定义

下列能力跨多个场景有价值，但不应立刻塞进最小 Core：

- **Concurrency Profile**：线程边界、snapshot/live view、访问冲突、取消和隔离；
- **Determinism Profile**：稳定查询/序列化顺序、tick、phase、barrier 和重放；
- **Resource Profile**：`ResourceId`、规范 URI、内容哈希、异步加载、依赖图、缓存和 lease；
- **Event Profile**：订阅生命周期、重入、批量/coalesce、回放和背压；
- **Plugin ABI Profile**：版本协商、能力发现、allocator、错误/字符串所有权、线程、quiesce 和卸载；
- **Replication Profile**：authority、revision、冲突解决和 canonical encoding；
- **Editor Profile**：undo/redo、dirty tracking、selection、字段 UI hints。

每个 Profile 应有自己的协议向量和启用成本，不能通过一个默认大对象接口强制所有使用者承担。

## 暂不补入公共协议

SparseSet、Archetype、对象中心布局、GC/refcount/arena、线程池、SIMD、GPU 调度、Scene/Actor/Node、Transform、Physics、Renderer、Network、Script、JSON/二进制具体格式，以及某种语言的 trait、宏、comptime、异常和 ABI 规则，都仍应留在实现或领域适配器中。

## 建议顺序

1. 先为 P0 的七项写语言无关测试向量；
2. 解决 `PersistentId` optional、strong/destroy 和 query view 三个现有歧义；
3. 再决定事务/事件是否进入 M0.1，或先作为通用 profile；
4. 用 Rust、Zig、C++ 参考实现验证同一批向量；
5. 只有跨实现一致后，才把相应内容从本研究分支提升到主分支。
