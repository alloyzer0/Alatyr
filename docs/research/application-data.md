# application-data 研究分支

状态：Research

本分支验证 Alatyr 是否能表达一个不依赖游戏引擎或物理模拟的普通应用数据模型。示例领域可以是项目配置、文档元数据、任务记录或用户定义的数据对象。

## 研究问题

1. 只有 Core、Schema 和 Persistence 时，是否能构造可用的数据对象；
2. `ObjectHandle`、`PersistentId` 和 `TypeId` 的分层是否清晰；
3. 固定 Schema 字段和动态扩展属性是否需要两条路径；
4. 未知类型是否可以保留并再次保存；
5. schema 版本迁移是否不依赖某种语言的内存布局；
6. Resource、Object 和 Component 的边界是否能在普通应用中成立；
7. Data 层是否能替换存储布局而不改变上层协议。

## 最小领域模型

候选对象：

```text
Project
  persistent_id
  name
  schema_version

Task
  title
  status
  priority
  optional custom fields

Document
  metadata
  references to other objects
```

这些只是测试数据，不应回收到通用 Core。

## 必须验证的流程

- 创建对象并分配运行时句柄；
- 保存并重新加载 PersistentId；
- 修改字段并应用默认值；
- 重命名字段后执行迁移；
- 加载未知 TypeId 并保持 opaque payload；
- 删除对象后验证 strong、weak、external 引用；
- 对象只拥有部分组件时，不产生未使用组件字段；
- 用另一种 ComponentStore 实现运行同一组协议测试。

## 不在本分支研究

- 编辑器 UI、场景树和 Prefab；
- 物理、渲染、网络和脚本；
- 最终序列化格式选型；
- Rust、Zig 或 C++ 的最终比较；
- 生产级数据库和并发事务。

## 产出标准

研究完成后必须产出：

1. 协议缺口清单；
2. 至少一组成功和失败测试向量；
3. 内存和 round-trip 基准；
4. 需要回收到 `master` 的跨领域决策；
5. 应继续留在 Adapter 或领域层的内容。
