# Alatyr master 分支与当前框架范围

状态：`Accepted for M0`

这份文档回答两个问题：`master` 现在应该保存什么，以及 Alatyr 的第一版通用框架应该定义什么。它不决定 Rust、Zig 或 C++，也不决定具体内存布局。

## 1. 两个范围

### M0：当前 master 基线

当前仓库以语言无关的协议、架构文档、决策记录和跨领域测试场景为主。它可以被阅读、评审和用于实现原型，但不声称已经提供生产级运行时。

M0 包含：

- 术语、边界和模块依赖；
- Core、Data、Schema、Persistence 的协议草案；
- 对象身份、引用、生命周期和错误语义；
- Schema、未知类型和版本迁移的测试场景；
- 分支、ADR、研究示例和合并门槛；
- 不绑定语言的协议测试向量和基准定义。

M0 暂不包含任何具体领域的完整实现。

### M1：第一版可运行框架

M1 在语言选型后实现最小参考运行时。只有下面四个模块进入稳定实现范围：

```text
Core         身份、生命周期、所有权、引用、错误模型
Data         ComponentStore、PropertyStore、Query、Access
Schema       TypeRegistry、Schema、FieldDesc、默认值、约束
Persistence  一种 round-trip 格式、引用、未知类型、简单迁移
```

Tools 和 Adapters 在 M1 只提供接口、测试夹具和最小示例，不实现完整编辑器或领域系统。

## 2. M1 的具体内容

### Core

Core 负责运行时对象的最小语义：

- `ObjectHandle`：运行时句柄，至少包含可检测复用的 generation；
- `PersistentId`：跨保存、加载和文件边界稳定的身份；
- `TypeId`：类型注册和序列化选择的身份；
- 创建、删除、存活检查和 generation 校验；
- 所有权锚点和引用种类：strong、weak、external；
- 对象删除、句柄失效和未知引用的确定结果；
- 结构化错误模型，禁止用未定义行为表示失败。

Core 不负责名称、Transform、场景树、渲染状态、物理状态、编辑器状态或动态属性字典。

### Data

Data 规定组件和属性的访问语义，而不是规定唯一布局：

- `ComponentStore<T>`：添加、移除、读取、写入和按访问模式查询；
- `PropertyStore`：保存可反射字段或动态扩展值；
- 固定强类型数据和动态 `Value` 数据分开；
- 组件未挂载时不产生实例字段；
- 查询结果中的对象失效、并发和修改规则明确；
- 存储实现可以是稀疏集合、连续数组、分页表或其他实现。

M1 只需要一种参考 ComponentStore 和一种可选 PropertyStore，不承诺最终使用 SparseSet、Archetype 或对象旁挂列表。

### Schema

Schema 负责描述类型和字段，不保存每个对象的实例值：

- `TypeDesc`：稳定类型标识、名称、版本和能力声明；
- `FieldDesc`：字段标识、值类型、默认值、约束和持久化/编辑标志；
- 类型注册、查找和冲突检测；
- 固定字段与动态字段的边界；
- 类型缺失、字段缺失和字段重命名的描述方式。

Schema 不实现 Inspector UI、不绑定某个序列化格式，也不要求所有类型都可编辑。

### Persistence

Persistence 负责把对象数据转换为可迁移的外部表示：

- `SerializedEnvelope`：`PersistentId`、`TypeId`、schema version、payload、外部引用；
- 至少一种 round-trip 格式；
- 默认值填充、字段重命名和简单版本迁移；
- 未知类型以 opaque payload 保留，或明确报告不可保存；
- 资源引用解析和缺失引用报告；
- 损坏数据、迁移失败和回滚结果可观察。

Persistence 不把内存地址、容器布局或语言 ABI 写入格式。

## 3. 仅定义接口的模块

### Tools

M1 只定义以下适配点：

- `Inspectable`：根据 Schema 枚举可见字段；
- `Validator`：返回结构化诊断；
- `EditOperation`：把修改转成可记录的操作；
- `Undo/Redo`：只约定操作边界，不实现完整事务系统。

不进入 M1 的内容：编辑器 UI、属性控件、场景视图、Prefab、资源浏览器和完整热重载。

### Adapters

Adapters 只通过公开协议接入外部领域，例如：

- 应用程序的数据模型；
- 游戏编辑器的场景树或 ECS；
- 物理模拟的批量组件和求解器；
- 资源导入、脚本、网络或渲染系统。

它们不能反向改变 Core 的身份、引用和生命周期语义。

## 4. 明确排除项

以下内容可以在 `research/*` 或 `examples/<domain>` 中验证，但不属于当前 master 或 M1：

- 渲染器、物理求解器、网络复制和多人编辑；
- 完整 ECS、Archetype 或场景树定案；
- 编辑器 UI、Prefab、完整 Undo/Redo 和资源导入管线；
- 脚本语言、代码热重载和动态库插件 ABI；
- 并发模型的最终承诺；
- 全局字符串字典式的万能属性系统；
- 生产级文件格式兼容承诺；
- 具体语言、宏、trait、comptime 或垃圾回收策略；
- 任何领域专用的 Transform、Node、Actor、RigidBody 或 Scene 语义。

## 5. M1 验收条件

M1 不以功能数量验收，而以语义和失败案例验收：

1. 对象删除后旧句柄能确定地失效；
2. 运行时句柄、持久化 ID 和 TypeId 不混用；
3. 未挂载组件不增加对象实例字段；
4. 至少一种固定 Schema 和一种动态属性路径可用；
5. 数据可以保存、加载并完成一次 schema 迁移；
6. 未知类型可以保留为 opaque 数据，或返回可诊断错误；
7. 外部引用、缺失引用和损坏数据有明确结果；
8. 至少两个不同领域示例无需修改 Core 语义即可接入；
9. Core、Data、Schema、Persistence 可独立测试；
10. 仓库可以从零构建并重复运行协议测试。

## 6. master 合并门槛

任何新增内容在合并到 `master` 前必须说明：

- 解决了哪个跨领域问题；
- 增加了哪些 API、内存、编译和运行时成本；
- 失败、迁移和未知类型如何处理；
- 为什么不能放在 Adapter 或领域示例中；
- 至少一个正向案例和一个边界案例；
- 协议测试或基准证据在哪里。

只能证明单一领域收益的实现留在研究分支或示例中。
