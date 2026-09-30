# application-data 测试向量

这些 JSON 文件先定义语义，不绑定实现语言或最终文件格式。实现只需要把自己的内部结果转换成相同的预期结果。

执行顺序建议：

1. `01-roundtrip.json`
2. `02-migration.json`
3. `03-unknown-type.json`
4. `04-references.json`

每个向量中的 `operations` 是行为描述，`expected` 是必须满足的结果。
