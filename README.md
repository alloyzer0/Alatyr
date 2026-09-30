# Alatyr

一个语言无关、可组合的对象与数据框架研究仓库。

## 命名约定

公共项目名和根命名空间使用完整的 `alatyr`。它比两字母缩写更容易保持唯一，也能让不同语言的实现保持一致：

```text
Rust       crate / module: alatyr
Zig        package / namespace: alatyr
C++        namespace alatyr
C#         Alatyr.*
```

只有在 C ABI、宏或生成符号等必须使用短前缀的地方，才使用 `al_`（宏使用 `AL_`）。不把 `ar` 作为主缩写，因为它与 augmented reality、array、archive 等常见含义冲突，而且无法自然对应 `Alatyr`。

它暂时不面向某个具体领域。目标是先确定一组稳定的基础协议，再通过独立的应用示例验证这些协议能否服务于：

- 普通应用的数据模型；
- 游戏引擎编辑器；
- 物理模拟和批量计算；
- 资源处理、导入和构建工具；
- 脚本、插件或动态扩展宿主。

## 仓库原则

`master` 只保留经过评估的通用基础协议和架构决策，不直接收纳某个领域的完整实现。

领域实现优先作为独立示例、适配器或短期研究分支存在。只有被多个领域验证、且不依赖某个领域语义的内容，才回收到 `master`。

语言实现暂不作为第一阶段决策。先用语言无关的接口、数据模型、测试场景和基准定义架构，再分别评估 Rust、Zig 或其他实现。

## 目录

```text
docs/
  architecture/    架构草案、术语和模块边界
  decisions/       ADR（架构决策记录）
examples/           面向具体领域的最小验证程序
```

## 分支与合并规则

推荐使用以下分支类型：

```text
master
  ├── research/editor-inspector
  ├── research/physics-simulation
  ├── research/application-data
  └── research/resource-pipeline
```

- `master` 是稳定基线，不把它当作所有领域代码的集成分支；
- `research/*` 用来验证领域假设，可以快速试错；
- 研究分支只有在形成可复用协议、测试或明确 ADR 后才合并；
- 不把领域特有的 `Transform`、场景树、物理约束或编辑器状态放进 Core；
- 领域分支长期存在时，优先拆成 `examples/<domain>` 或独立仓库，避免分支永久漂移。

## 第一个阶段

当前阶段只做架构研究，不做完整产品。第一批产物应包括：

1. 术语表和边界；
2. Core / Data / Schema / Persistence / Tools / Adapters 的模块草图；
3. 身份、引用、生命周期和错误模型；
4. Schema、未知类型和版本迁移策略；
5. 至少两个领域的最小原型；
6. 内存、遍历、序列化和构建裁剪基准。

详见 [架构草案](docs/architecture/architecture-draft.md) 和 [ADR-0001](docs/decisions/ADR-0001-repository-and-baseline.md)。
