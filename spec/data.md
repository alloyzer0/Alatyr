# Data 协议

Data 把对象身份与对象数据分开。组件只在对象拥有该组件时进入对应存储。

## 组件存储

参考操作：

```text
attach(handle, component)
detach(handle, component_type)
get(handle, component_type)
query(access_pattern)
```

`query` 的布局可以由实现决定。协议只规定返回的对象句柄、访问权限、失效对象和修改行为。

## 属性

固定 Schema 字段和动态属性是两条不同路径：

- 固定字段可以生成强类型访问；
- 动态字段使用 Value、FieldId 或其他类型擦除表示；
- 不支持动态属性的对象不应携带通用字典；
- 属性值不复制 FieldDesc，字段描述属于 Schema。
