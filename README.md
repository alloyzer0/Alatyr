# Alatyr

一个语言无关、可组合的对象与数据协议。

Alatyr 不预设游戏引擎、编辑器、物理模拟或普通应用中的任何一种对象模型。它先定义跨领域成立的身份、生命周期、组件、Schema 和持久化语义，再由领域适配器提供具体能力。

## Master 基线

`master` 只保留：

- 仓库说明和贡献规则；
- 语言无关的协议描述；
- 已接受的核心架构决策。

当前协议分为：

```text
Core         身份、生命周期、引用、错误
Data         组件和查询访问语义
Schema       类型、字段、版本和约束
Persistence  外部表示、迁移和未知类型
Extension    领域服务和适配器边界
```

实现、测试向量和领域研究保留在 `research/*` 分支，只有跨领域验证后才回收到 `master`。

## 目录

```text
spec/                 语言无关的公共协议
docs/decisions/       已接受的架构决策
CONTRIBUTING.md       仓库变更和合并规则
```

领域研究的完整材料保留在对应的 `research/*` 分支，不属于当前 `master` 文件树。

## 研究分支

```text
master
  ├── research/application-data
  ├── research/physics-simulation
  └── research/<future-domain>
```

研究分支用于验证领域假设。领域类型、存储布局、求解器索引、编辑器 UI、渲染、脚本和网络能力不能直接进入 Core。

## 命名

公共命名空间使用 `alatyr`。只有 C ABI、宏或生成符号使用 `al_` / `AL_`。

Rust、Zig、C++ 或其他语言的实现尚未决定。先以协议为准，再比较实现成本和运行时特性。

协议入口见 [spec/README.md](spec/README.md)，核心决策见 [ADR-0003](docs/decisions/ADR-0003-core-protocol.md)。
