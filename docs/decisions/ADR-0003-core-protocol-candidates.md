# ADR-0003：跨领域可提炼的核心协议候选

- 状态：Proposed
- 日期：2026-10-01
- 证据：application-data、physics-simulation 两个研究分支

这份 ADR 只提出候选协议，不代表已经合并到 `master`。候选协议分为 Core、Data、Schema、Persistence 和 Extension 五层，避免把所有能力都称为 Core。

## 1. Core：运行时身份和生命周期

### 1.1 身份

```text
ObjectHandle  运行时句柄，包含 slot/index 和 generation
PersistentId  跨保存、加载和文件边界稳定的身份
TypeId        类型注册和 Schema 查找的身份
```

三者职责不同：

- `ObjectHandle` 可以失效，不能作为持久化身份；
- `PersistentId` 可以跨进程存在，不能保证对象当前存活；瞬时对象可以没有 PersistentId；
- `TypeId` 描述类型，不代表某个实例。

### 1.2 生命周期

最小操作：

```text
create(type_id, persistent_id) -> ObjectHandle
is_alive(handle) -> bool
describe(handle) -> (type_id, persistent_id)
destroy(handle) -> Result
```

删除后，旧句柄必须确定地失效。generation 复用不能让旧句柄访问新对象。

### 1.3 生命周期协调

对象删除必须有一个明确的协调边界，保证属性、组件和外部服务不会继续持有有效对象状态。候选形式：`World`、`ObjectRuntime`、destroy transaction 或事件协议，尚未决定具体形式。

## 2. Core：引用语义和错误模型

### 2.1 引用

公共协议至少区分：

```text
strong    目标缺失时报告 MissingReference
weak      目标缺失时返回 empty/None
external  由资源或外部系统解析，失败可诊断
```

引用保存时使用 PersistentId 或资源 ID，不能写入内存地址、slot 或 solver index。

### 2.2 错误

跨领域都需要可诊断的错误类别：

- InvalidHandle；
- UnknownType；
- UnknownField；
- MissingReference；
- SchemaMismatch；
- MigrationFailed；
- CorruptData；
- AccessConflict。

错误至少携带对象、类型、字段、版本或数据位置等上下文。语言可以使用 Result、异常或错误码，但不能静默丢失数据。

## 3. Data：组件和查询协议

这部分不是最小 Core，但已经被两个方向证明适合作为公共 Data 层候选。

### 3.1 组件操作

```text
attach(handle, component_type, value)
detach(handle, component_type)
get(handle, component_type)
```

未挂载组件不产生实例字段。组件值属于实例，组件类型的描述属于 Schema 或注册表。

### 3.2 查询

```text
query(required_components, access_mode) -> handles / view
```

协议应定义：组件缺失、对象失效、读写权限和查询期间修改的结果。它不应规定 SparseSet、Archetype、连续数组或对象中心布局。

查询顺序暂不作为公共不变量。需要确定性时，可以由 Adapter 显式请求稳定顺序或自行排序。

## 4. Schema：类型和字段描述协议

Schema 是类型级数据，实例只保存当前值。

```text
TypeDesc {
    type_id
    stable_name
    schema_version
    capabilities
    fields[]
}

FieldDesc {
    field_id
    value_type
    default_value / provider
    constraints
    flags
}
```

Schema 层需要支持：

- 类型注册和冲突检测；
- 字段默认值和约束；
- 固定字段与动态字段的显式区别；
- 字段重命名、删除和版本迁移描述。

动态字段不应成为所有对象的默认字符串字典。

## 5. Persistence：外部表示协议

Persistence 可以独立于 Core，但它的最小 envelope 语义适合进入公共协议：

```text
SerializedEnvelope {
    persistent_id
    type_id
    schema_version
    payload
    external_references
}
```

必须定义：

- round-trip 的身份保持；
- 默认值填充；
- 版本迁移和失败回滚；
- 未知类型的 opaque 保留或可定位错误；
- 外部引用缺失；
- 损坏数据诊断。

具体 JSON、二进制、文本格式和压缩方式不属于公共协议。

## 6. Extension：服务和适配器协议

序列化器、校验器、Inspector、物理服务、渲染服务、脚本和网络系统都应通过扩展协议接入：

```text
register_service(type_or_capability, service)
register_adapter(domain, adapter)
```

它们不能让 Core 认识领域类型，也不能把领域内部索引当作公共身份。

## 7. 不属于核心协议的内容

- Object tree、Scene、Actor、Node、Transform、RigidBody；
- SparseSet、Archetype、连续数组等具体布局；
- solver index、render index、GPU handle；
- Inspector UI、Undo/Redo、Prefab；
- 碰撞求解、渲染、网络同步和脚本语言；
- 并发、线程池、SIMD 和 GPU 调度；
- 动态插件 ABI 和代码热重载；
- 查询默认排序；
- 某种编程语言的 trait、宏、comptime、GC 或 ABI。

## 8. 回收 master 的建议条件

在两个领域的研究结果基础上，可以考虑把以下内容回收到 `master`：

1. Core 身份、生命周期、引用和错误语义；
2. Data 的 attach/detach/get/query 访问协议；
3. Schema 的 TypeDesc、FieldDesc 和版本语义；
4. Persistence envelope、迁移和未知类型处理；
5. 对应的语言无关测试向量。

具体实现、布局、动态属性策略和领域服务仍留在 reference implementation 或 Adapter。
