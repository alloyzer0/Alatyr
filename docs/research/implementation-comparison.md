# Alatyr 实现语言比较：Rust、Zig 与 C++

- 状态：研究材料，不是语言选型决议
- 范围：对照 M0 的 Core、Data、Schema、Persistence 和 Extension 协议，比较三种候选实现的表达成本与风险
- 证据：`experiment/rust-reference`、`experiment/zig-reference`、`experiment/cpp-reference` 的最小参考原型
- 结论约束：当前原型用于验证协议能否被表达，不用于宣布性能、生态或生产可用性上的胜负

## 1. 研究问题和边界

Alatyr 的公共协议故意把运行时句柄、持久化身份、类型身份、组件访问、Schema 和外部表示分开。实现语言需要提供这些语义的可检查表达，但协议不能依赖某种语言的所有权、宏、`comptime`、异常或 ABI 规则。

本比较回答以下问题：

1. 能否清楚地表达句柄世代、组件访问和持久化 envelope？
2. 当组件采用运行时注册、动态 Schema 或未知类型保留时，类型系统会带来什么帮助和成本？
3. 如何实现可替换的 ComponentStore，而不让公共句柄暴露存储布局？
4. Schema/反射、迁移、错误和生命周期如何落到实现中？
5. 构建、跨平台发布和 C ABI 插件如何影响框架边界？

下文的“支持”表示语言或生态可以实现该能力，不表示标准库已经内置该能力。三者都需要显式的协议描述、注册表和测试向量。

## 2. 当前证据

| 原型 | 分支和提交 | 运行方式 | 已覆盖的协议切片 |
| --- | --- | --- | --- |
| Rust | `experiment/rust-reference`，`e94ff9c` | `cargo run --manifest-path prototypes/rust-reference/Cargo.toml` | generation 句柄、`PersistentId`/`TypeId`、组件 attach/detach/get/query、默认值与简单迁移、未知 envelope 保留 |
| Zig | `experiment/zig-reference`，`71d4835` | `zig build run` | slot+generation、两种身份、组件访问、默认值与迁移、未知 envelope payload 保留 |
| C++ | `experiment/cpp-reference`，`1719832` | `./prototypes/cpp-reference/run.sh` | generation 句柄、两种身份、组件访问、默认值与迁移、未知 envelope 保留 |

三份原型都采用对象中心的最小实现。Rust 使用 `HashMap<TypeId, Value>`，C++ 使用 `unordered_map<TypeId, Value>`，Zig 使用固定槽位和组件位掩码；它们没有实现生产级的 SparseSet、Archetype、连续列存储或批量查询。因此“代码较短”“运行较快”都不能从这组原型推出。

## 3. 快速比较

| 维度 | Rust | Zig | C++ |
| --- | --- | --- | --- |
| 协议表达 | `struct`、`enum`、`Result`/`Option`、trait；语义边界容易进入类型签名 | `struct`、error union、optional、`comptime`；语义直接且显式 | `struct`/class、`variant`、`optional`、模板或 `expected`；表达自由但依赖约定 |
| 内存与别名安全 | 编译器强制所有权和借用；运行时句柄有效性仍需检查 | 手动生命周期和指针规则；错误集合和可选值受类型检查 | RAII 管理资源，但裸指针、迭代器失效和未定义行为仍需纪律 |
| 错误和生命周期 | `Result` 与 `Drop` 适合分层传播；借用检查可能限制查询期间的修改 | error union、`defer`/`errdefer` 清晰；资源和失效引用主要靠实现约束 | RAII 很成熟；异常、C++23 `std::expected`（或第三方实现）、错误码可选，但跨边界不能抛异常 |
| 组件存储 | 泛型存储安全；运行时类型擦除和多组件可变查询需要设计借用 API | `comptime` 易生成布局；运行时注册、`anyopaque` 和 vtable 需要手动维护 | 模板、分配器和 `pmr` 选择最多；ABI、迭代器和指针失效风险最高 |
| Schema/反射 | 无内置运行时字段反射；derive/procedural macro 或显式描述符 | 无内置运行时反射；`@typeInfo` 可在编译期生成描述符 | C++20 无可移植字段反射；RTTI 不等于 Schema，通常需要宏或显式描述符 |
| Persistence | `Result`、字节容器和生态库成熟；未知 payload 可作为原始 bytes 保留 | 字节和 allocator 语义明确；格式、校验和生命周期全部由应用决定 | 库选择最多；需避免直接序列化对象内存和跨版本 ABI |
| 构建与依赖 | Cargo 统一、锁文件和测试体验好；泛型/宏会增加编译成本，crate 多为源码分发 | `zig build` 和交叉编译简单，C 互操作自然；包和缓存策略仍需项目制定 | 生态和现有引擎最广；CMake/Meson/Bazel、vcpkg/Conan 等选择多且不统一 |
| C ABI/插件 | `#[repr(C)]`、`extern "C"`、`cdylib` 可用；不得让 panic 或 Rust 布局穿过 ABI | `export fn`、`callconv(.C)` 直接；allocator、错误码和插件卸载仍需约定 | 需用 `extern "C"` 包住稳定 façade；不能跨边界传 STL、异常或编译器私有布局 |

这张表只显示工程约束，不是加权评分。权重取决于目标是安全的长期核心、可嵌入的低层库，还是已有 C++ 工具链的领域适配器。

## 4. 按协议层比较

### 4.1 Core：身份、生命周期和引用

三种语言都可以把 `ObjectHandle` 表示为 `{slot, generation}`，并在每次访问时检查槽位是否存活且 generation 相等。删除时递增 generation，槽位复用不会让旧句柄访问新对象。这个约束本身是运行时协议，不会被任何一种语言自动证明。

Rust 的 `Copy` 小句柄和私有槽位很适合把句柄做成廉价值类型；`Result<_, Error>` 可以把 `InvalidHandle` 传播到调用者。对象内部若保存引用，借用规则能阻止一部分悬空引用，但 `ObjectHandle` 仍只是可失效的值，不能把 `is_alive` 检查当成永久保证。查询返回借用视图时，借用检查会迫使 API 明确“查询期间是否允许销毁或修改”。这会增加设计成本，却能把许多别名错误提前变成编译错误。

Zig 可用小结构和 error union 直接表达同样的接口。它不隐式管理对象或分配器，适合需要精确控制生命周期的运行时；但指向槽位、组件列或临时查询结果的指针在删除、扩容和迁移后是否仍有效，必须由 ComponentStore 的文档和实现保证。`defer`/`errdefer` 能覆盖函数范围内的资源回收，不能代替跨函数的所有权协议。

C++ 可以用值类型句柄、RAII 和 C++23 `std::expected`（或第三方 `expected`）/异常/错误码实现同一语义，且方便接入已有引擎对象。但 RAII 只管理拥有的资源，不会自动识别旧句柄；如果公共 API 返回裸指针或迭代器，就会把槽位重用、容器扩容和删除后的失效规则暴露给调用者。建议 C++ 实现也把句柄访问集中到 `World`/运行时边界，避免让外部直接持有内部地址。

`strong`、`weak` 和 `external` 引用在三者中都应以显式结构或 tagged value 表示。持久化时只写 `PersistentId`/资源 ID，不能写 slot、solver index 或地址。语言的引用/指针类型不能替代这一层协议。

### 4.2 Data：ComponentStore 和查询

M0 只规定 `attach`、`detach`、`get` 和 `query` 的语义，没有规定布局。生产实现至少会在以下方案之间取舍：

- 对象中心 map：实现最快，随机访问直观，但遍历和缓存局部性较弱；
- 每类组件一个稀疏/密集存储：适合按组件查询，需要处理 entity-to-row 映射和删除搬移；
- Archetype/列式布局：多组件查询高效，但结构变更和借用视图复杂；
- 外部服务存储：适合物理或 GPU 资源，公共对象只保存稳定身份或 opaque handle。

Rust 的泛型和 trait 可以把 `ComponentStore<T>`、稀疏集合和列式存储做成类型安全模块。问题出现在运行时注册的 `TypeId`：组件值需要 `Any`/trait object、手写 vtable 或序列化类型擦除；多组件可变查询不能简单返回任意数量的 `&mut`，通常需要查询规划器、分裂借用、临时批处理或受控 `unsafe`。这些限制不会阻止高性能实现，但必须在 API 中明确访问模式和修改规则。

Zig 可通过 `comptime` 为已知组件生成紧凑列和批量查询，也可用运行时 `TypeId` 加字节缓冲区、对齐信息和函数表做类型擦除。布局与分配器完全由实现掌握，便于做 SoA、定制内存和跨语言 ABI；代价是组件值的对齐、销毁、移动和指针失效都要手动维护，错误只能部分由编译器发现。

C++ 的模板、`std::pmr`、自定义 allocator 和现有 ECS 库提供最广的布局选择，迁移渐进式实现也较容易。模板实例化、类型擦除和异常安全会增加复杂度；容器扩容或 swap-remove 造成的引用/迭代器失效必须写入 ComponentStore 契约。C++ 适配器若需要与旧引擎共享内存，还要额外规定 allocator 和线程边界。

三种实现都应把 `ObjectHandle` 与 solver/render index 分开。批量查询应返回句柄或稳定行票据，不应把内部 row/index 当作持久化身份。

### 4.3 Schema 和反射

M0 的 `TypeDesc`/`FieldDesc` 是协议数据，不等同于语言反射。它们至少需要稳定 `TypeId`、字段 ID、值类型、默认值、约束、能力标志和版本迁移描述；固定字段与动态字段必须明确区分。

Rust 没有稳定的运行时字段反射。常见做法是 derive/procedural macro 在编译期生成 `TypeDesc`、访问器和序列化代码，或手写静态描述符再注册到表中。`serde` 解决许多格式编解码问题，但不自动提供稳定字段 ID、未知字段保留策略或迁移事务；这些仍需 Alatyr 层的描述和测试。宏生成的错误信息、增量编译和跨 crate 注册是需要评估的工程成本。

Zig 的 `@typeInfo` 能在 `comptime` 遍历结构字段并生成描述符，适合减少重复声明；生成结果若要在运行时按 `TypeId` 查找，仍需注册表、命名策略和版本数据。Zig 的反射主要是编译期能力，不能自动发现动态插件中新类型；插件需要显式导出注册函数或 C ABI 描述表。

C++20 没有可移植的标准字段反射。RTTI 可以识别多态类型，却不能可靠地列出字段、默认值或稳定 Schema。生产代码通常用宏、模板 traits、代码生成、手写 `FieldDesc`，或依赖外部反射/序列化库。宏侵入和多编译器差异是长期成本；如果使用 C++26 或第三方反射提案，也不能把尚未统一的能力写进跨语言协议。

因此，三者都应把“生成/注册 TypeDesc”作为可替换实现层，并对生成结果运行同一份 Schema 向量测试。不要把语言的类型名、内存布局或 RTTI 名称直接当作稳定 `TypeId`。

### 4.4 Persistence、迁移和未知类型

`SerializedEnvelope` 的稳定边界是 `persistent_id`、`type_id`、`schema_version`、原始 payload 和外部引用。具体 JSON、二进制、压缩或加密格式不由语言决定。加载流程需要区分：已知类型直接解码；已知类型但旧版本先迁移；未知类型保留 envelope 或返回可定位错误；损坏数据不能静默变成默认对象。

Rust 的 `Vec<u8>`、切片和 `Result` 适合实现分层解析。serde/bincode/自定义格式可以复用，但必须确认未知字段和未知类型的原始字节能否无损保留。迁移函数应返回新值或错误，若要支持事务回滚，不能在原对象上先写入一半结果。资源所有权和外部引用解析仍是应用层协议。

Zig 直接处理字节切片和 allocator，容易把未知 payload 保存在拥有明确的缓冲区中，也容易因 allocator 约定不一致产生悬空数据。标准库不会替应用选择稳定格式、校验、整数溢出策略或版本迁移；这些都应成为测试向量和错误模型的一部分。

C++ 有最丰富的格式库和现有工具，但直接对对象内存做二进制 dump 会把 padding、指针、编译器布局和 endianness 锁进文件，不能满足 Alatyr 的跨版本目标。使用 `vector<std::byte>`/显式 reader-writer、RAII 临时值和 C++23 `std::expected`（或第三方实现）/错误码可以建立安全边界。异常不得跨 C ABI 或插件卸载边界传播。

三种语言都需要单独验证以下行为：默认值填充、字段重命名/删除、迁移失败回滚、未知类型 opaque round-trip、缺失外部引用和损坏数据位置。当前原型只覆盖默认值、简单版本检查和未知 payload 保留。

## 5. 构建、依赖和发布

### Rust

Cargo 提供统一的包描述、锁文件、特性、测试、examples、workspace 和 `cdylib`/`staticlib` 目标。对框架仓库来说，这使协议向量和多个 reference crate 容易纳入 CI，`cargo fmt`/`clippy`/`test` 也较一致。泛型单态化、过程宏和大型依赖树可能拉长冷编译；增量构建、编译缓存和 workspace 拆分需要规划。crates.io 的典型交付仍是源码，目标平台二进制缓存可以通过 CI artifact、sccache 或发行包补充，不能把 Cargo 默认行为当作系统级二进制包管理。

### Zig

`build.zig` 把编译、交叉编译、C 头文件和自定义步骤放在同一套脚本中，适合生成小型 C ABI 库和多目标测试。allocator、优化级别和目标三元组可显式传递。包管理和全局二进制缓存的组织方式不如 Cargo 统一，项目应固定依赖版本、缓存策略和离线构建流程。Zig 同样通常从源码构建依赖；它解决的是编译器和目标管理，不自动提供稳定的跨平台二进制包生态。

### C++

C++ 可以复用现有引擎、图形、物理和工具链，编译器和调试器覆盖最广；代价是项目需要在 CMake、Meson、Bazel 或其他系统之间作出选择，并处理 vcpkg、Conan、系统包或自带依赖的组合。二进制包能减少构建时间，但 ABI、编译器版本、标准库、运行时库和编译选项不一致会造成隐性不兼容。C++20 modules 尚不能替代所有现有头文件和包管理流程。Alatyr 若提供 C++ SDK，应把编译器/标准库矩阵和 allocator 边界作为发布契约。

三种语言都可做可复现构建，但策略不同：Cargo 依赖 lockfile，Zig 依赖项目锁定的 build graph 和工具链版本，C++ 需要额外锁定编译器、包描述和二进制缓存。框架最终应把“源码构建”和“预构建 artifact”视为发行渠道选择，而非协议层属性。

## 6. C ABI 和插件边界

如果 Alatyr 需要让编辑器、物理、脚本或外部工具以插件方式接入，最小稳定边界应是版本化的 C ABI：

```c
typedef struct al_object_handle { uint64_t slot; uint64_t generation; } al_object_handle;
typedef struct al_api { uint32_t abi_version; /* function pointers */ } al_api;
al_status al_plugin_init(const al_api* host, al_plugin_api* out);
```

具体字段、错误码、字符串所有权、allocator、线程和卸载顺序需要另行定义。插件不应传递 Rust trait object、Zig 私有结构、C++ STL 容器、异常或指向可移动组件列的裸指针。对象和 payload 的释放必须回到创建它的 allocator，或由 host 提供释放函数。

- **Rust**：使用 `#[repr(C)]`、固定宽度整数、`extern "C"` 和 `cdylib`。FFI 函数应捕获 panic 后返回状态码；`String`、`Vec`、trait object 和带 drop 的结构不跨边界。可用 cbindgen 生成头文件，但生成文件仍需 ABI 审查。
- **Zig**：`export fn` 与 `callconv(.C)` 可直接导出 C 符号，结构布局可显式标注。不能让 Zig allocator、error union 或 optional 的私有表示跨边界；把错误转换为版本化状态码和诊断回调。
- **C++**：用窄的 `extern "C"` façade 包住内部 C++ 实现，禁止 STL、异常、RTTI 指针和模板实例跨边界。即使 host 与插件都由 C++ 编译，类布局和标准库 ABI 也不能视为稳定协议。

在这三种语言中，C ABI 的真正难点都不是导出函数，而是内存拥有权、错误传播、线程模型和卸载时仍存活的回调。应先定义 `al_`/`AL_` 的版本化 ABI，再决定内部语言。

## 7. 原型的不足和不能从中推出的结论

当前三个原型的共同限制：

1. 没有使用同一份可执行的跨语言协议向量；断言覆盖相同主题，但输入、错误和输出格式仍由各自代码决定。
2. 组件存储是对象中心最小切片，未比较 SparseSet、Archetype、列式布局、swap-remove、批量写入或缓存行为。
3. 动态字段、字段约束、稳定字段 ID、重命名/删除迁移、迁移事务和回滚尚未实现。
4. strong/weak/external 引用、缺失引用诊断和销毁协调边界尚未完整覆盖。
5. Persistence 只保留内存中的 envelope/payload，没有选定格式，也没有损坏数据、大小上限、校验、endianness、压缩或外部引用解析测试。
6. 没有并发查询、访问冲突、线程安全、任务调度、allocator 争用或长时间运行测试。
7. 没有测量编译时间、增量编译、二进制大小、内存占用、查询吞吐、迁移成本或跨平台差异；不能据此比较性能。
8. 没有实现 C ABI、插件加载/卸载、热重载、符号版本或多编译器矩阵。
9. Zig 原型使用固定 16 槽位和嵌入式组件字段，主要验证语法、error union 和协议含义；它不是通用的动态存储实现。
10. Rust 与 C++ 原型使用字符串类型 ID 和 map，忽略了稳定 ID 编码、哈希碰撞、注册冲突和大规模对象的内存成本。

特别是，三份原型都在成功路径上打印“OK”。这只能证明选取的示例可以运行，不能证明错误模型、异常安全、资源回收或跨 ABI 行为完整。

## 8. 建议的下一轮公平比较

在做语言选型前，应把测试输入和期望输出独立于语言保存，例如 `tests/vectors/*.json` 或确定性的二进制向量。每种语言都读取同一份向量，并至少增加以下实验：

1. 固定组件集和动态组件集各实现一个 ComponentStore；分别测对象中心、稀疏/密集和列式布局。
2. 对同一个对象执行创建、销毁、槽位复用和 stale handle 访问，验证错误类别和上下文。
3. 用至少两个 Schema 版本覆盖默认值、字段重命名、字段删除、迁移失败和回滚。
4. 对未知类型执行 load → opaque store → save round-trip，确认 payload 与外部引用不被破坏。
5. 加入 strong/weak/external 引用和缺失目标，比较错误传播是否一致。
6. 使用相同的 C ABI 头文件编译 host 与插件，测试字符串、payload、allocator、回调和卸载顺序。
7. 在代表性目标上记录冷/热编译、增量编译、二进制体积、峰值内存、批量 query、组件迁移和序列化吞吐。
8. 至少覆盖 Linux、macOS、Windows 的静态库、动态库和 sanitizer/调试构建。

测试报告应把“协议一致性”“实现安全性”“性能/构建成本”和“生态适配”分开，避免一个维度的优势掩盖另一个维度的缺陷。

## 9. 暂定解读（不构成选型决议）

- **Rust 作为语义参考实现**：如果优先让句柄访问、错误传播和资源所有权获得编译期约束，Rust 最容易把一部分不变量放入 API；动态组件、借用视图、宏生成 Schema 和 C ABI 需要额外设计。
- **Zig 作为显式低层实现**：如果优先可控的布局、allocator、交叉编译和直接 C 互操作，Zig 能保持实现简单透明；Schema 注册、指针失效、资源拥有权和运行时类型擦除需要项目自己建立纪律。
- **C++ 作为生态/集成实现**：如果必须接入现有 C++ 引擎、物理、图形或编辑器，C++ 的库和工具覆盖面最广、渐进集成最容易；公共核心仍需严格封装指针、异常、容器 ABI 和构建矩阵，以控制原有复杂度。

因此当前更稳妥的策略是：继续维护语言无关的 `spec/` 和跨语言向量；先选择一门语言做可验证的参考实现，再用 C ABI 或协议向量让其他语言成为适配器。参考实现的语言可以在完成下一轮公平实验后决定，不应因为当前最小原型的代码风格而锁定架构。
