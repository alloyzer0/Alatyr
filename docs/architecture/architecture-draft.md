# 通用可扩展 Object / Data 框架架构草案

状态：`Draft v0.2`。这份文档用于整理 Unreal Engine、Unity、Godot 的可复用设计，并把目标从“游戏引擎对象系统”扩大为“可组合对象运行时 + 类型/Schema 元数据协议 + 可选持久化和工具服务”。它不对最终架构作定案。所有带有“待决策”的项目都应经过原型、基准测试和失败案例验证后再选择。

## 1. 目标与边界

目标是提供一个可以被应用程序、游戏引擎编辑器、物理模拟、资源工具、数据处理工具和其他系统复用的框架，覆盖：

- 稳定的对象身份和类型身份；
- 可选的属性、组件和能力；
- 类型级元数据与编辑器 Inspector；
- 序列化、版本迁移和资源引用；
- 编辑器功能与运行时功能的分层；
- 不使用某项能力时，尽量不产生实例级内存和计算成本。

暂不把渲染、物理、网络复制、脚本语言、场景树和完整 ECS 作为本框架的既定组成部分。它们可以作为后续组件或适配层接入。框架的价值应来自稳定的协议和可替换的模块，而不是预先覆盖所有应用场景。

这里的 `Item` 暂时只是占位名，不应直接成为最终公共抽象。一个通用框架需要明确区分：可在运行时存在的 `Object`、可保存和共享的 `Resource/Asset`、附着到对象上的 `Component/Data`，以及提供行为的 `Service/Capability`。它们可以共享 TypeId、Schema 和引用协议，但不必共享一个重量相同的基类。

## 2. 从三个引擎得到的观察

### Unreal Engine

Unreal 通过 UHT 和宏生成反射信息，核心概念包括 `UObject`、`UClass`、`FProperty`（旧版本称 `UProperty`）、`UStruct` 和 `UActorComponent`。编辑器属性面板、序列化、默认对象和许多工具都共享这套类型元数据。

可复用的思想：

- 类型元数据是正式的一等数据，而不是编辑器临时扫描出来的结果；
- 属性标志和元数据可以驱动编辑器、序列化、复制和校验；
- Actor 与 Component 的组合方式适合把可选能力拆出核心对象；
- 对象身份、对象生命周期和序列化系统需要一起设计。

需要警惕的成本：

- 代码生成和构建流程与反射强耦合；
- `UObject` 生命周期、垃圾回收、默认对象和编辑器状态会扩大基础对象模型；
- 如果所有对象都进入同一个对象体系，轻量工具对象也会承担不必要的运行时成本。

### Unity

Unity 以 `GameObject + Component` 组织场景对象，Inspector 主要依赖序列化字段和编辑器扩展。`ScriptableObject` 承担可共享、可独立保存的资源数据，场景和 Prefab 保存对象及组件数据，并通过 GUID、fileID 和引用关系维持身份。

可复用的思想：

- 组合优先于庞大的继承树；
- 场景对象、资源对象和组件对象应有不同的存储及生命周期；
- 类型定义、实例数据、资源身份和 Prefab/实例覆盖需要分开；
- 编辑器可以通过属性标记、PropertyDrawer 和自定义 Inspector 扩展。

需要警惕的成本：

- 序列化规则是字段驱动的，支持范围和例外较多；
- 托管对象、原生对象、编辑器对象和运行时对象之间存在边界；
- Prefab 覆盖、默认值和域重载会使变更追踪复杂化；
- 通用动态属性容器容易退化成昂贵的字符串字典。

### Godot

Godot 以 `Object`、`Node` 和 `Resource` 分层，ClassDB 保存引擎类型信息，`Variant` 承担动态值，Inspector 可以读取 `PropertyInfo`，脚本还可以通过 `_get_property_list()` 动态提供属性。场景和 Resource 使用带有外部资源、子资源和 UID 的序列化格式。

可复用的思想：

- 属性列表可以由对象动态提供，而不必完全依赖静态字段扫描；
- Node 的树状所有权关系适合编辑器中的场景组织；
- Resource 与 Node 分开，说明“可保存数据”和“场景实例”不应混为一谈；
- `Variant + PropertyInfo` 可以作为编辑器与运行时之间的动态边界。

需要警惕的成本：

- `Variant` 和字符串属性访问会带来类型检查及间接访问成本；
- Node 树很直观，但会把数据组织、生命周期和场景层级耦合起来；
- 动态属性和脚本属性必须处理运行时与编辑器不一致的情况。

## 3. 草案中的概念分层

草案不把所有功能放入一个 `Item` 结构体，而是分为四层：

```text
ObjectId / ItemId
        │
        ├── CoreStore              必需的身份和生命周期信息
        ├── ComponentStores        可选的高频、强类型实例数据
        ├── PropertyStore          可选的可反射或动态属性值
        └── Resource / AssetStore  可保存、可共享的外部数据

TypeRegistry
        ├── TypeDesc               类型级描述
        ├── Schema / FieldDesc      字段和编辑器元数据
        ├── Serializer              序列化及反序列化处理器
        ├── Migration               版本迁移处理器
        └── EditorAdapter           Inspector、校验和编辑操作
```

### 3.1 核心身份

候选形态：

```text
ObjectCore {
    object_id
    type_id
    lifecycle / ownership reference
    optional flags or generation
}
```

核心对象只放所有实例都需要的数据。名称、Transform、物理状态、编辑器状态、属性字典和序列化器都不默认放进这里。

### 3.2 可选组件和能力

需要区分“实例数据能力”和“服务能力”：

- 实例数据能力：Transform、Physics、Renderable、CustomProperties；
- 服务能力：Serialize、Inspect、Validate、Migrate、Replicate。

实例数据可以放进 `SparseSet<T>`、分页数组、Archetype 或其他组件存储。服务能力放在 `TypeRegistry` 或模块注册表中，不在每个对象上保存函数指针或 trait object。

### 3.3 类型元数据

类型描述可以包含：

```text
TypeDesc {
    type_id
    stable_name
    schema_id / schema_version
    flags or capability set
    constructor / destructor adapter
    serializer adapter
    migration adapter
    editor adapter
}

FieldDesc {
    field_id
    name
    value_type
    flags: editable / runtime / transient / replicated / required ...
    default value or default provider
    constraints and editor hints
}
```

元数据属于类型；属性值属于实例；序列化器属于类型注册表。这三者不应复制到每个对象中。

### 3.4 属性系统

属性需要区分三种情况：

1. **固定强类型状态**：例如 Transform，适合代码生成和连续存储；
2. **可反射字段**：类型固定，但需要 Inspector、序列化和校验；
3. **用户自定义属性**：类型和字段运行时才确定，才使用动态 `Variant/Value` 容器。

对固定 schema，可以用字段槽位或生成的结构体；对稀少覆盖，可以只保存相对类型默认值的 override；只有真正支持自定义属性的实例才进入动态 PropertyStore。

### 3.5 序列化边界

序列化建议围绕类型和 schema 版本，而不是把内存布局直接写盘：

```text
SerializedObject {
    object_id
    type_id
    schema_version
    payload
    external references
}
```

序列化流程需要支持：类型缺失、字段缺失、字段重命名、旧版本迁移、默认值填充、外部资源引用和损坏数据报告。

序列化不应自动意味着可编辑；可编辑也不应自动意味着必须持久化。它们是可以独立注册的服务能力。

## 4. 可选功能的成本模型

“不需要时不占成本”需要分三个层次讨论：

### 构建级

编辑器、反射、调试、序列化和脚本模块可以通过构建配置完全移除。需要决定是使用编译特性、独立模块、独立二进制，还是插件。

### 类型级

只有注册了某项能力的类型才进入对应的 `TypeRegistry`。例如只有可保存的类型才注册 Serializer，只有可编辑的类型才注册 Schema 和 EditorAdapter。

### 实例级

只有实际拥有某个组件的对象才进入组件存储。避免在每个核心对象上放 `Option<HashMap>`、`Option<String>` 或大量空字段。

需要接受一个现实：只要支持运行时动态发现能力，就会有少量注册表、类型检查或间接调用成本。目标应是把成本限制在边界操作，避免进入渲染、物理和批处理等高频路径。

## 5. 尚未确定的架构选项

下面列出需要通过后续评估决定的项目。此处不选答案。

### D0：`Item` 的职责

- 只表示可编辑的对象；
- 表示所有运行时实体；
- 表示资源、实体和资产的统一抽象；
- 拆成 `Entity`、`Resource`、`Asset`、`Object` 多种根类型。

### D1：对象组织模式

- 纯对象树，类似 UObject / Node；
- GameObject + Component；
- ECS / SparseSet / Archetype；
- 核心对象树加组件存储的混合模式。

比较标准：编辑器可用性、批处理性能、对象引用、生命周期、序列化复杂度。

### D2：对象身份

- 紧凑索引加 generation 的运行时句柄；
- 全局 UUID；
- 运行时句柄和持久化 UUID 并存；
- 路径、名称或对象树地址。

需要测试删除后悬空引用、保存后重载、跨文件引用、网络复制和多人编辑。

### D3：类型身份

- 编译器 TypeId；
- 稳定字符串名；
- UUID；
- schema hash；
- 组合方案：运行时 ID + 持久化名称/UUID。

### D4：属性表示

- 代码生成的固定 schema；
- 动态 `Variant/Value` 属性包；
- 固定字段和动态扩展字段的混合模式；
- 外部 schema 驱动。

### D5：可选数据存储

- SparseSet；
- Archetype；
- 每类型连续数组；
- 每对象旁挂组件列表；
- 面向编辑器的稀疏 Map。

需要用高密度和低密度两种工作负载分别测量内存、遍历和删除成本。

### D6：反射/元数据生成

- Rust 过程宏；
- Zig comptime；
- 外部 schema 和代码生成；
- 手工注册；
- 多种方式共存。

需要比较编译时间、错误提示、增量构建、插件注册、跨语言和热重载。

### D7：序列化格式

- 面向编辑的文本格式；
- 紧凑二进制格式；
- 文本源文件加构建期二进制缓存；
- 版本化自定义格式；
- 外部通用格式。

### D8：schema 版本演进

- 只允许向前兼容；
- 显式 migration 函数；
- 字段级 rename/default/deprecate 规则；
- 由外部 schema 工具生成迁移；
- 不保证旧数据兼容。

### D9：编辑器与运行时边界

- 同一类型和同一二进制；
- 编辑器元数据编译进运行时；
- 编辑器独立进程，通过协议连接运行时；
- 编辑器模块只在工具构建中存在。

### D10：所有权和引用

- 强引用、弱引用和句柄；
- 引用计数；
- tracing GC；
- arena / world 所有权；
- 手动生命周期。

需要明确循环引用、跨场景引用、资源缓存和对象销毁时的行为。

### D11：编辑修改与 Undo/Redo

- 命令日志；
- 属性变更快照；
- 对象级事务；
- 事件溯源；
- 只在编辑器层实现。

### D12：插件与动态注册

- 静态链接注册；
- 动态库插件；
- 脚本注册；
- 外部 schema 包；
- 不支持运行时新增类型。

### D13：热重载

- 不支持；
- 只支持资源热重载；
- 支持类型 schema 热重载；
- 支持代码和组件布局热重载。

热重载会直接影响对象身份、迁移、函数指针和内存布局，应该单独验证。

### D14：引用和资源模型

- 所有引用都用对象 ID；
- 资源使用 GUID，运行时对象使用句柄；
- 路径只作为编辑器显示，不作为稳定身份；
- 允许内嵌子资源和外部资源。

### D15：并发模型

- 单线程编辑器模型；
- 读写锁；
- 分阶段更新；
- 消息队列；
- 任务图和批量组件访问。

### D16：运行时动态性

- 类型和属性在编译期固定；
- 类型固定、字段可动态发现；
- 运行时可注册新类型；
- 脚本拥有动态对象层。

### D17：语言绑定

- Rust derive + trait registry；
- Zig comptime + 生成元数据；
- 外部 schema 作为语言无关层；
- C ABI 作为插件边界；
- 多语言共存。

### D18：部署配置

- Editor、Runtime、Server、Tool 分开构建；
- 通过 feature 裁剪；
- 通过插件裁剪；
- 允许运行时保留完整反射。

## 6. 建议的多轮评估流程

### 第 0 轮：需求和场景矩阵

先固定场景，不讨论 Rust 或 Zig：

1. 10 万个只有核心身份的对象；
2. 少量对象拥有稀疏属性；
3. 高频 Transform 和 Renderable 批处理；
4. Inspector 修改字段并执行 Undo/Redo；
5. 保存、加载和 schema 迁移；
6. 外部资源、子资源和跨文件引用；
7. 缺失插件或未知类型时打开旧项目；
8. Editor、Runtime、Server 三种构建；
9. 多线程运行时访问组件；
10. 需要脚本或动态属性的对象。

每个场景先定义可接受的内存、延迟、启动时间和错误恢复目标。

### 第 1 轮：纸面设计

只定义不超过十个核心接口和不变量，例如：

- ID 不可复用，或复用必须通过 generation 检测；
- 元数据与实例值分离；
- 序列化不依赖内存地址；
- 删除对象后所有引用有确定结果；
- 未使用的组件不进入实例存储。

此轮不实现完整编辑器。

### 第 2 轮：实现两个或三个最小原型

至少对比：

- 组件存储方案；
- 固定 schema 与动态属性包；
- 运行时句柄与持久化 UUID；
- 反射生成方案。

原型使用相同的场景和接口，避免每种方案用不同标准比较。

### 第 3 轮：性能和内存基准

测量：

- 空对象的字节数；
- 100 万次创建和删除；
- 组件遍历和随机访问；
- 属性读取、修改和动态查找；
- 保存、加载和迁移；
- Inspector 枚举属性；
- 增量编译和全量编译；
- Editor 与 Server 的二进制大小。

### 第 4 轮：失败和演进测试

重点测试：

- 字段重命名、删除和类型变化；
- 旧类型或插件缺失；
- 文件损坏或版本跳跃；
- 对象删除后的弱引用；
- 循环资源引用；
- 并发读写和编辑器事务失败；
- 热重载后旧对象迁移。

### 第 5 轮：加权决策

为每个待决策项打分。初始权重可以包括：

```text
可维护性       __%
编辑器体验     __%
运行时性能     __%
内存占用       __%
数据兼容       __%
工具链复杂度   __%
生态和插件     __%
实现风险       __%
```

权重必须由实际项目目标决定，不能直接沿用 Unreal、Unity 或 Godot 的权重。

## 7. 暂时只保留的工作假设

这些不是最终架构，只是下一轮原型可以采用的共同接口：

1. `ObjectId`、`TypeId` 和持久化资源 ID 分开建模；
2. 核心对象保持很小，可选数据采用外置组件存储；
3. Schema 是类型级数据，PropertyValue 是实例级数据；
4. Serializer、Migration、Inspector 是注册表服务，不进入每个对象；
5. 编辑器元数据可以在 Runtime/Server 构建中被裁剪；
6. 动态反射只出现在编辑器、序列化、脚本等边界，不进入高频批处理；
7. 固定强类型字段、可反射字段和用户自定义字段使用不同的数据路径。

这些假设如果在原型或基准测试中失败，应及时撤回，而不是为保持一致性继续扩大实现。

## 8. 通用化后的架构定位

通用化并不意味着让所有场景共用一套最大对象模型。更合理的目标是定义一个很小的内核协议，再让不同应用选择能力模块和存储布局。这样既能服务游戏编辑器，也能服务物理模拟或普通应用，同时避免把 Node、Actor、GameObject、资源和动态脚本对象硬塞进同一个抽象。

### 8.1 术语边界

| 概念 | 负责什么 | 不应默认负责什么 |
|---|---|---|
| `Object` | 运行时身份、生命周期、类型和可选数据关联 | 持久化格式、编辑器面板、具体业务行为 |
| `Resource/Asset` | 可保存、可共享、可被引用的数据 | 必然拥有场景生命周期或每帧更新 |
| `Component/Data` | 某个对象的实例状态 | 全局类型注册和服务实现 |
| `Service/Capability` | 序列化、校验、编辑、查询、迁移等行为 | 被复制到每个对象实例 |
| `Schema/TypeDesc` | 类型、字段、约束、能力和版本的描述 | 保存每个实例的当前值 |

例如，物理模拟可以把 `RigidBody` 作为 Component，把 `PhysicsWorld` 作为外部 Service；应用程序可以只使用 `Object + Resource + Serializer`；游戏编辑器再添加 `Schema + Inspector + Undo`。这些组合都不需要改变 Core 的身份和引用协议。

### 8.2 建议的模块边界

```text
Layer 0  Core
    ObjectId / TypeId / 生命周期 / 所有权 / 引用句柄 / 错误模型

Layer 1  Data
    ComponentStore / PropertyStore / Query / Access

Layer 2  Schema
    TypeRegistry / Schema / FieldDesc / 默认值 / 约束 / 能力声明

Layer 3  Persistence
    Serializer / Deserializer / Migration / ResourceResolver / 未知类型处理

Layer 4  Tools
    Inspector / Validation / Undo-Redo / 文本格式 / 资源浏览 / 热重载

Layer 5  Adapters
    ECS / 场景树 / 渲染 / 物理 / 网络 / 脚本 / 宿主应用集成
```

依赖方向应该向下：Tools 可以依赖 Schema 和 Persistence，Adapters 可以依赖 Core、Data 或 Schema；Core 不应反向依赖编辑器、文件格式、渲染或某个引擎的生命周期。`ComponentStore` 只提供访问协议，SparseSet、Archetype、按类型数组和编辑器 Map 都可以作为替换实现。

### 8.3 “不使用就不付费”的可验证定义

不要把目标表述成所有场景的绝对零成本，而应定义可测预算：

- Core 空对象不超过约定的 `N` 字节；
- 未启用模块不增加实例级字段和每帧扫描；
- Schema、Serializer 和 EditorAdapter 是类型级或模块级成本；
- 动态属性、字符串查找和间接调用只出现在编辑、保存、脚本等边界；
- 高频数据可以选择连续布局，低频冷数据可以选择稀疏或分页布局；
- 移除某模块后，构建产物、启动时间和注册表规模应有可测变化。

## 9. 取舍不是“一个架构全覆盖”

框架应该提供能力组合，而不是试图同时成为对象树、ECS、文档数据库和反射运行时。可以先定义几个用于评估的应用画像：

| 应用画像 | 主要需求 | 可以舍弃的能力 |
|---|---|---|
| 普通应用数据模型 | 稳定 ID、Schema、校验、持久化 | 高频批处理、场景树、实时热更新 |
| 游戏编辑器 | 对象/资源、Inspector、Undo、引用、迁移 | Server 的完整编辑元数据 |
| 物理模拟 | 连续组件布局、查询、确定性、批量更新 | 动态字段、复杂编辑器服务 |
| 资源处理工具 | Resource/Asset、依赖图、版本迁移、离线构建 | 每帧生命周期、对象树 |
| 脚本或插件宿主 | 动态注册、未知类型、隔离、错误恢复 | 极致的静态布局和零间接成本 |

如果一个决策无法同时满足这些画像，应保留 SPI 或适配层，而不是在 Core 中折中出一个所有场景都不理想的实现。

## 10. 优先级更高的六个架构决策

原来的 `D0-D18` 适合作为完整清单，但初期不应同时决定。建议先锁定下面六个高风险问题，其余决策建立在它们之上：

1. **身份、引用和销毁**：运行时句柄与持久化 ID 是否并存；强引用、弱引用、外部引用和对象删除后的结果是什么。
2. **Object、Resource、Component、Service 的边界**：哪些东西拥有生命周期，哪些东西只保存数据，哪些行为由注册表提供。
3. **Schema 与动态性**：字段是否编译期固定，是否允许运行时注册类型，未知类型是否以 opaque payload 保留。
4. **ComponentStore 的替换协议**：Core 是否只依赖 query/access 接口，从而允许稀疏、连续、分页和 archetype 布局共存。
5. **持久化和迁移**：数据格式、schema 版本、字段重命名、缺失插件、迁移失败回滚和错误报告如何定义。
6. **运行时与工具边界**：Editor、Runtime、Server、Tool 是否独立构建，编辑器元数据是否可以完全裁剪。

并发、热重载、插件 ABI、网络复制和脚本绑定可以在这六项稳定后再单独决策。它们会放大前六项的错误，但通常不应该反过来决定 Core 的形状。

## 11. 语言无关的最小协议

在讨论 Rust、Zig、C++ 或其他语言之前，可以先写出语言无关的协议：

```text
ObjectHandle {
    runtime_id
    generation
}

PersistentId {
    namespace
    stable_id
}

TypeDesc {
    type_id
    schema_version
    capabilities
    fields[]
}

ComponentStore {
    add(handle, component)
    remove(handle)
    get(handle)
    query(access_pattern)
}

PersistenceService {
    save(value, schema)
    load(bytes, schema_registry)
    migrate(value, from_version, to_version)
}
```

协议只规定语义、错误和不变量，不规定内存布局、宏、trait、comptime、垃圾回收或文件编码。语言层的实现可以为静态类型路径生成快速代码，也可以为动态插件路径提供注册表和间接访问。

## 12. 对现有评估流程的调整

第 0 轮的场景矩阵应去掉对游戏引擎的隐含假设，至少加入以下非游戏场景：

- 普通应用中加载未知字段并保持原样再保存；
- 物理模拟中按组件批量读取和写入；
- 资源工具中跨文件依赖和增量构建；
- 插件缺失时以只读或 opaque 形式打开数据；
- 只需要 Core 的最小部署产物。

每个候选架构都要回答同一组问题：

1. 空对象、稀疏对象和高密度组件分别占用多少内存；
2. 没有 Schema、Persistence、Tools 时是否能构建和运行；
3. 未知类型和旧版本数据是否可恢复；
4. 删除、复制、迁移和并发访问是否有明确语义；
5. 复杂度是集中在可替换模块，还是扩散到所有调用方。

最终决策应记录“选择了什么、为了什么场景、放弃了什么、如何测量”，而不是只记录某个引擎采用了什么模式。

## 13. 参考资料

- Unreal Engine Reflection System: <https://dev.epicgames.com/documentation/en-us/unreal-engine/reflection-system-in-unreal-engine>
- Unity Script Serialization: <https://docs.unity3d.com/Manual/script-Serialization.html>
- Unity ScriptableObject: <https://docs.unity3d.com/Manual/class-ScriptableObject.html>
- Godot Object: <https://docs.godotengine.org/en/stable/classes/class_object.html>
- Godot Resource: <https://docs.godotengine.org/en/stable/classes/class_resource.html>
- Godot `_get_property_list()`: <https://docs.godotengine.org/en/stable/classes/class_object.html#class-object-private-method-get-property-list>
