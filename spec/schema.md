# Schema 协议

## 类型

`TypeDesc` 至少描述：

```text
type_id
stable_name
schema_version
capabilities
fields[]
```

## 字段

`FieldDesc` 至少描述：

```text
field_id
name
value_type
default_value or provider
constraints
flags
```

Schema 是类型级数据，实例只保存当前值和必要的覆盖信息。

## 版本

版本迁移必须说明来源版本、目标版本、失败结果和是否可重复执行。字段重命名、删除、类型变化和默认值填充不能依赖字段在内存中的地址。
