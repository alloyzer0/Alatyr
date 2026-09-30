# 领域示例

领域示例用于验证协议，不是 master 的产品功能。建议示例至少覆盖两个不同画像：

- `application-data`：普通应用的数据对象、Schema、保存和迁移；
- `physics-simulation`：批量组件访问和连续计算数据；
- `editor-model`：Inspector、诊断和可选 Undo；
- `resource-pipeline`：资源身份、依赖和未知类型保留。

示例不能通过修改 Core 隐含语义来解决领域问题。它需要说明使用了哪些协议、放弃了哪些能力，以及哪些内容仍然应该留在 Adapter。
