# Super 只读群 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：私聊查询和修改。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super readonly list` 命令

### `/super readonly list` - CHAT

**完整格式**：`/super readonly list`

**所需权限组**：`super`

查看独立只读群名单。

## `/super readonly add` 命令

### `/super readonly add` - CHAT

**完整格式**：`/super readonly add 群号`

**所需权限组**：`super`

设为只读群，阻止发送。

## `/super readonly remove` 命令

### `/super readonly remove` - CHAT

**完整格式**：`/super readonly remove 群号`

**所需权限组**：`super`

解除只读，不补发旧提醒。

## 使用规则与示例

三个命令均仅私聊可用，GROUP 不开放。`list` 查看只读群名单，`add` 设置只读，`remove` 解除只读。

Readonly 独立于身份组，阻止群发送、群提醒及管理修改群 DDL；Super 也不能绕过。私聊可查看只读群任务。解除只读后不补发已经跳过的旧提醒。
