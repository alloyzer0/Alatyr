# application-data 示例

这个目录预留给普通应用数据模型的最小验证程序。它应只依赖 Alatyr 的 Core、Schema、Data 和 Persistence 协议，不引入游戏引擎语义。

第一版实现需要覆盖：

- `Project`、`Task` 和 `Document` 三种测试类型；
- 固定 Schema 字段和少量动态扩展字段；
- 保存、加载、字段重命名和默认值迁移；
- 未知类型的 opaque 保留；
- 对象引用和删除后的失效结果。

具体语言实现和文件格式暂不在此 README 中决定。

当前分支有一个临时向量执行器，可以运行：

```bash
python3 examples/application-data/reference_runner.py
```

它只验证协议语义，不代表最终的 Alatyr API，也不用于性能结论。
