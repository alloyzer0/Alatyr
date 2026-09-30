# application-data / physics-simulation 跨领域比较

状态：Research，未形成 master 合并决策。

## 两个领域都需要的语义

| 候选公共协议 | application-data | physics-simulation | 当前判断 |
|---|---:|---:|---|
| Runtime handle 与 PersistentId 分离 | 是 | 是 | 候选 Core 协议 |
| TypeId / TypeRegistry | 是 | 可选但有用 | 候选 Schema 协议 |
| 对象创建、删除、generation 失效 | 是 | 是 | 候选 Core 协议 |
| Component attach / detach / get | 可选 | 是 | 候选 Data 协议 |
| Component query | 可选 | 是 | 候选 Data 协议，语义需继续收敛 |
| 删除时清理附属数据 | 是 | 是 | 需要公共生命周期协调语义 |
| strong / weak / external 引用 | 是 | 可选 | 候选 Core/Reference 协议 |
| Schema 版本和默认值 | 是 | 初始状态可能需要 | 候选 Schema 协议 |
| Persistence envelope | 是 | 资源/初始状态需要 | 候选 Persistence 协议 |

## 只在单个领域中出现的能力

| 能力 | 所属领域 | 暂时位置 |
|---|---|---|
| 动态字段 | application-data | Property Adapter 或可选 PropertyStore |
| 未知插件类型 opaque 保留 | application-data | Persistence Adapter，可能进入公共错误协议 |
| Schema 字段迁移 | application-data | Persistence/Schema |
| 高密度批量积分 | physics-simulation | Physics Adapter |
| solver index | physics-simulation | Physics Adapter |
| stable query order | physics-simulation 可能需要 | Query 选项或 Adapter |
| 碰撞、约束、求解 | physics-simulation | 永不进入 Core |

## 当前可以提出的跨领域候选

两个领域共同支持以下方向：


1. Core 只拥有身份、生命周期和错误语义；
2. Data 通过可替换 ComponentStore 提供 attach/detach/get/query；
3. Schema 和实例值分离；
4. 外部服务可以使用 ObjectHandle，但不要求 Core 认识服务内部索引；
5. 删除需要一个明确的协调边界；
6. Query 的布局和实现不应进入公共协议。

## 仍不能合并的内容

以下内容还没有跨领域证据：

- 动态属性是否属于 Data 核心，还是单独的 Property Adapter；
- Query 顺序是否是公共不变量；
- dense index 映射是否值得进入通用协议；
- Persistence 是否应该进入最小 Core，还是作为独立模块；
- 并发、批量写入和事务边界；
- 任何具体内存布局。

## 下一步决策材料

在回收 master 前，还需要：

1. 把两个领域使用的操作名称对齐；
2. 为删除协调写一个不绑定存储布局的协议测试；
3. 明确 Query 的最小语义和顺序承诺；
4. 为 Persistence 增加一个物理初始状态或资源引用向量；
5. 创建候选 ADR，区分 `master protocol`、`reference implementation` 和 `adapter`。
