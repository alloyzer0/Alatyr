# 错误模型

错误必须能区分至少以下类别：

- InvalidHandle：句柄已经失效或 generation 不匹配；
- UnknownType：类型未注册；
- UnknownField：字段未注册或已移除；
- MissingReference：外部引用无法解析；
- SchemaMismatch：版本或类型不匹配；
- MigrationFailed：迁移失败；
- CorruptData：外部数据损坏；
- AccessConflict：访问权限或并发契约冲突。

错误应携带对象、类型、字段、版本和数据位置等上下文。具体语言可以使用 Result、异常、错误码或诊断集合，但不能把失败降级为未定义行为。
