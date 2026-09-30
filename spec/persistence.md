# Persistence 协议

外部表示至少包含：

```text
PersistentId
TypeId
schema_version
payload
external_references
```

## 未知类型

加载方不认识 TypeId 时有两个允许结果：

1. 保留完整 envelope 和 payload，允许再次保存；
2. 返回带有原始身份、类型和位置的结构化错误。

静默丢弃未知数据不符合协议。

## 迁移

迁移失败必须返回可定位的诊断，并保证原始输入仍然可恢复，或明确说明事务已经回滚。序列化不依赖内存布局、指针、编译器 ABI 或容器实现。
