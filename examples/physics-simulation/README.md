# physics-simulation 示例

这是一个只用于协议验证的最小物理数据模型。它不实现碰撞检测或求解器，只验证：

- 高密度组件查询；
- 批量积分边界；
- 组件移除；
- ObjectHandle 与 solver index 分离；
- 删除后 solver index 可复用但对象身份不能复用。

运行向量：

```bash
python3 examples/physics-simulation/reference_runner.py
```
