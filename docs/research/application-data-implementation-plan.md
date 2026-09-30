# application-data 实施计划

本计划只验证协议和边界，不在这一阶段决定最终实现语言或生产级 API。

## 阶段 A：协议执行器

用一个可快速修改的临时参考实现读取 `test-vectors/application-data/*.json`。它只负责验证语义，不进入 `master`，也不作为最终性能实现。

必须先实现的概念：

```text
TypeRegistry
ObjectStore
ComponentStore
PropertyStore
ReferenceResolver
MigrationRegistry
PersistenceEnvelope
```

执行器先支持四条闭环：

1. 创建、设置、保存、加载；
2. Schema 版本迁移；
3. 未知类型 opaque 保留；
4. 对象删除和引用失效。

## 阶段 B：发现协议缺口

运行向量后记录：

- 哪些错误需要携带更多上下文；
- PersistentId 和 ObjectHandle 的转换边界；
- strong、weak、external 引用是否需要不同的保存规则；
- 动态属性是否需要 FieldId、类型标签和存在性标记；
- 迁移是否需要事务和回滚；
- 未知类型是否可以被修改，还是只能只读转发。

每个缺口先改协议文档和测试向量，再改参考实现。

## 阶段 C：两个存储实现

保持同一组行为测试，比较两种布局：

1. 以对象为中心的组件映射；
2. 按组件类型连续或稀疏存储。

比较空对象、稀疏对象、高密度组件、随机访问和删除后的清理成本。此阶段不把任一布局写成 Core 语义。

## 阶段 D：第二个领域

在 `research/physics-simulation` 或 `research/resource-pipeline` 中复用同一协议。第二个领域的目的是验证：

- Core 没有偷偷携带 application-data 语义；
- Schema 和 Persistence 的公共部分确实跨领域成立；
- 组件访问协议没有被普通应用的动态属性需求污染。

## 阶段 E：回收或隔离

研究完成后，将结果分为：

- `master`：跨领域协议、错误语义、测试向量和有证据的参考实现；
- `examples`：只服务某个领域的对象和流程；
- 新 ADR：改变公共不变量的决策；
- 保留在 research：未解决或只有单领域证据的方案。

## 阶段完成条件

- 四个 application-data 向量全部通过；
- 至少两个 ComponentStore 布局通过同一组行为测试；
- 至少一个未知类型和迁移失败案例可诊断；
- 第二个领域可以不修改 Core 语义接入；
- 形成一份“保留到 master / 留在 Adapter / 放弃”的决策记录。
