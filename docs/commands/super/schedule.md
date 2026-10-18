# Super 提醒调度 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：读取当前机器人提醒安排。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super schedule` 命令

### `/super schedule` - CHAT

**完整格式**：`/super schedule [user QQ号|group 群号]`

**所需权限组**：`super`

查看当前机器人全部或指定会话的未来待发提醒。

### `/super schedule` - GROUP

**完整格式**：`/super schedule [user QQ号|group 群号]`

**所需权限组**：`super`

须先真实 @机器人。查看当前机器人全部或指定会话的未来待发提醒。

## 使用规则与示例

`/super schedule` 不带参数列出当前机器人全部用户及群的未来待发提醒，按下一次提醒时间排序。`user QQ号` 仅筛选该用户个人会话，`group 群号` 仅筛选该群。

按 DDL 显示所属会话、设置者、通知对象、截止时间及未来 pending 提醒节点；已发送、取消、失败、过期节点不显示。已取消、全部退订及无剩余提醒的 DDL 不显示。

CHAT 和 GROUP 均支持全部或指定会话，结果发回当前会话。仅查询当前平台与机器人账号，查询不改变状态，实际发送仍受 Readonly 约束。

```text
/super schedule
/super schedule user 111
/super schedule group 3333
```
