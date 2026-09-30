# application-data 示例

这个目录预留给普通应用数据模型的最小验证程序。它应只依赖 Alatyr 的 Core、Schema、Data 和 Persistence 协议，不引入游戏引擎语义。

第一版实现需要覆盖：

- `Project`、`Task` 和 `Document` 三种测试类型；
- 固定 Schema 字段和少量动态扩展字段；
- 保存、加载、字段重命名和默认值迁移；
- 未知类型的 opaque 保留；
- 对象引用和删除后的失效结果。

具体语言实现和文件格式暂不在此 README 中决定。
