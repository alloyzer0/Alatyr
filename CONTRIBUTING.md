# Contributing to Alatyr

## 变更分类

每个变更必须标注为以下之一：

- `protocol`：语言无关的公共语义或不变量；
- `reference`：对已有协议的参考实现；
- `experiment`：只用于验证假设的实验；
- `adapter`：具体领域、宿主或工具集成。

`experiment` 和 `adapter` 优先进入 `research/*` 或 `examples/`，不能直接进入 master。

## master 合并检查

提交前回答：

1. 这是哪个跨领域问题？
2. 公共协议新增了什么表面？
3. 增加了多少内存、编译和运行时成本？
4. 失败、迁移、未知类型和回滚如何处理？
5. 为什么不能放在 Adapter？
6. 是否有正向和边界测试？

只能证明单一领域收益的内容留在研究分支。

## 命名

公共命名空间使用 `alatyr`。只有 C ABI、宏或生成符号使用 `al_` / `AL_`。
