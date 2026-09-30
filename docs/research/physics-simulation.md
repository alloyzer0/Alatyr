# physics-simulation 研究分支

状态：Research

本分支验证 Alatyr 是否能承载高密度、批量访问和确定性更新的物理模拟数据，同时不把物理语义写入 Core。

## 研究问题

1. ObjectHandle 是否可以作为稳定的外部身份，而让求解器使用独立的 dense index；
2. ComponentStore 是否能表达 Transform、Velocity、Mass 等高密度组件；
3. Query 是否能同时支持批量遍历和随机访问；
4. 删除对象后，组件存储和求解器索引如何协调；
5. 查询结果顺序是否需要稳定性保证；
6. 物理求解器是否可以完全作为 Adapter/Service 存在；
7. 动态属性、Schema 和 Persistence 是否可以保持在边界，而不进入每步求解。

## 最小领域模型

```text
ObjectHandle       Alatyr 运行时身份
RigidBody          质量、睡眠状态、求解器索引
Transform          位置、旋转
Velocity           线速度、角速度
Collider           形状资源引用
PhysicsWorld       物理求解器和批量更新服务
```

这些类型只属于本分支。能回收到 master 的只能是对组件查询、引用和生命周期的通用协议。

## 必须验证的流程

- 创建对象并挂载多个高密度组件；
- 按 `Transform + Velocity` 查询并批量更新；
- 使用 ObjectHandle 映射到独立 solver index；
- 删除对象并释放所有组件及 solver index；
- 组件移除后查询结果立即变化；
- 重复运行相同输入得到相同迭代顺序和输出；
- 物理服务不要求 Core 认识 `RigidBody` 或 `Collider`；
- 保存/加载只处理资源和初始状态，不保存求解器内部指针。

## 不在本分支研究

- 碰撞检测和约束求解算法；
- SIMD、GPU、线程池和最终内存布局；
- 网络同步和回放格式；
- 编辑器 Inspector；
- Rust、Zig 或 C++ 的最终选择。

## 产出标准

1. 领域向量和行为测试；
2. 至少一种批量查询参考实现；
3. ObjectHandle 与 solver index 的生命周期报告；
4. 顺序、删除和组件稀疏度的基准；
5. “回收到 master / 留在 Physics Adapter / 放弃”的决策记录。
