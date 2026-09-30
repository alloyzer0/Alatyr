# Extension 协议

Extension 是领域能力接入 Alatyr 的边界，不属于最小 Core。

服务或适配器可以注册在类型、能力或领域命名空间下：

```text
register_service(capability, service)
register_adapter(domain, adapter)
```

典型扩展包括：

- Inspector、Validator、Undo/Redo；
- PhysicsWorld、Renderer、ScriptRuntime；
- 资源导入、网络复制和宿主应用集成。

扩展必须通过公开的 Core、Data、Schema 或 Persistence 协议访问对象。扩展内部的 solver index、GPU handle、场景节点或线程模型不能成为 Core 的身份或生命周期语义。

扩展可以声明能力和成本，例如是否需要 Schema、PersistentId、动态字段或批量查询。未启用扩展时，Core 不应增加实例级字段或每帧扫描。
