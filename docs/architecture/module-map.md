# Alatyr 模块地图

```text
                    ┌────────────────────┐
                    │      Adapters      │
                    │ app / editor / sim │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │       Tools        │
                    │ inspect / validate │
                    │ undo / diagnostics │
                    └─────────┬──────────┘
                              │
       ┌──────────────────────▼──────────────────────┐
       │                  Persistence                 │
       │   serialize / migrate / resolve / preserve  │
       └──────────────────────┬──────────────────────┘
                              │
       ┌──────────────────────▼──────────────────────┐
       │                    Schema                   │
       │ type registry / fields / versions / flags  │
       └──────────────────────┬──────────────────────┘
                              │
       ┌──────────────────────▼──────────────────────┐
       │                     Data                   │
       │ component stores / properties / queries    │
       └──────────────────────┬──────────────────────┘
                              │
       ┌──────────────────────▼──────────────────────┐
       │                     Core                   │
       │ identity / lifetime / ownership / errors   │
       └─────────────────────────────────────────────┘
```

依赖方向只能向下。Core 不依赖文件格式、编辑器、物理、渲染或宿主应用。

## 依赖规则

| 模块 | 可以依赖 | 不应依赖 |
|---|---|---|
| Core | 标准库和基础内存/错误抽象 | Data、Schema、Persistence、Tools、领域语义 |
| Data | Core | 具体编辑器、文件格式、渲染和物理 |
| Schema | Core、Data 的抽象 | UI、具体文件编码 |
| Persistence | Core、Schema、Data 访问协议 | 具体领域对象 |
| Tools | Schema、Persistence、Data 访问协议 | Core 中的编辑器状态 |
| Adapters | 任意公开协议 | 直接修改 Core 的隐含语义 |
