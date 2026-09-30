# Core 协议

## 身份

Alatyr 区分三种身份：

```text
ObjectHandle  运行时句柄，可检测 generation 复用
PersistentId  跨保存和加载稳定的身份
TypeId        类型注册和 Schema 查找的身份
```

任何一个身份都不能代替另外两个身份。运行时句柄可以失效，PersistentId 可以跨进程存在，TypeId 可以在没有实例时存在。

## 生命周期

Core 至少提供：

```text
create(type) -> ObjectHandle
is_alive(handle) -> bool
destroy(handle) -> Result
```

销毁对象后，旧句柄必须返回确定的失效结果，不能访问新对象。

## 引用

引用至少区分：

- strong：拥有或保持目标存活；
- weak：目标销毁后变为失效；
- external：指向外部资源或外部系统，解析失败可报告。

具体引用计数、GC、arena 或手动释放策略不由本协议决定。
