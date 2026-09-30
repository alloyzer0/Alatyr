# physics-simulation 当前发现

## 已验证

- `ObjectHandle` 可以作为求解器外部身份，而 solver index 可以独立分配和复用；
- 多组件查询可以只返回同时拥有所需组件的对象；
- 组件移除后，后续查询结果立即变化；
- 没有 Velocity 的对象不会被积分操作修改；
- 求解器不需要让 Core 认识 RigidBody、Transform 或 Collider。

## 当前向量结果

```text
01-batch-query.json             PASS
02-component-removal.json       PASS
03-solver-index-lifecycle.json  PASS
```

这些是语义向量，不是求解器性能测试。参考实现中的顺序来自插入顺序，是否把顺序稳定性写入公共协议仍未决定。

## 暴露出的协议问题

### Query 的结果顺序

物理模拟、回放和测试可能需要确定性顺序；某些并行实现则希望自由重排。需要决定：

- Core 只保证集合语义；
- Query 提供显式的 stable order 选项；
- 由 Adapter 在需要时排序；
- 或把顺序标识写入协议。

### Solver index 的生命周期

当前示例允许 solver index 复用，但未定义：

- 组件删除与 solver index 回收的事务边界；
- 失败时如何回滚映射；
- 物理服务是否拥有 index，还是由外部 Store 注入；
- 多个求解器实例是否共享对象身份。

这些内容应该留在 Physics Adapter，除非第二个领域也需要相同的 dense-index 映射协议。

## 暂不下结论

当前结果只支持将批量 Query、组件生命周期和外部服务边界保留为候选公共协议。它还不足以决定 Archetype、SIMD、并发或物理专用存储布局。
