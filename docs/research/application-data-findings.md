# application-data 当前发现

## 已验证

- Runtime handle 使用 generation 后，删除并复用槽位不会让旧句柄访问新对象；
- PersistentId、TypeId 和 ObjectHandle 可以保持独立；
- Schema 默认值可以在加载阶段补全；
- 字段重命名迁移可以重复执行而不继续改变结果；
- 未注册类型可以作为完整 opaque envelope 保留；
- strong reference 在目标删除后返回 MissingReference；
- 组件查询不要求组件存储采用某一种布局。

## 暴露出的协议问题

### 删除的协调者

当前参考模型中，ObjectStore、PropertyStore 和 ComponentStore 是独立对象。删除 Object 后，调用方必须显式清理组件和属性。需要决定：

- 由 `World` 或 `ObjectRuntime` 作为生命周期协调者；
- 由 Store 订阅 destroy 事件；
- 由句柄失效后惰性清理；
- 或要求领域层显式执行删除事务。

这不是某个存储布局的问题，而是 Core/Data 之间的公共生命周期协议。

### 未知类型的可编辑性

当前只支持 opaque 保留和再次转发。仍需决定未知类型是否可以：

- 只读显示；
- 修改原始 payload；
- 通过通用字段层编辑；
- 只能等待插件恢复后再编辑。

### 动态字段的范围

当前 Schema 可以声明动态字段，但还没有定义字段 ID、值类型标签、默认值和未知字段保留方式。下一轮不能直接使用通用字符串字典，而应先增加向量。

## 暂不下结论

这些发现还不足以决定 Rust、Zig、C++，也不足以决定 SparseSet、Archetype 或对象中心布局。下一步应在保持相同协议测试的前提下添加第二种 ComponentStore，并补充删除协调和动态字段向量。
