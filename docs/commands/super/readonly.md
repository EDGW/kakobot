# Super 只读群 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：私聊查询和修改。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super readonly list` 命令

### `/super readonly list` - CHAT

**完整格式**：`/super readonly list`

**所需权限组**：`super`

列出当前配置中所有 Readonly 群，显示群名及群号，空名单显示为空。此命令只查询，不改变只读状态；仅私聊可用。全局 admin 也可使用普通入口 `/readonly list`。

```text
/super readonly list
```

## `/super readonly add` 命令

### `/super readonly add` - CHAT

**完整格式**：`/super readonly add 群号`

**所需权限组**：`super`

将 `群号` 加入只读名单，群号为必填正整数；仅私聊可用。

Readonly 独立于身份组，阻止向该群发送消息和 DDL 提醒，并禁止通过 Super 管理修改该群 DDL；Super 也不能绕过。群中的 DDL 命令不处理，私聊查询该群任务仍允许。

更改持久化并记录审计，成功后在当前私聊返回群名及确认；不修改该群角色授权。

```text
/super readonly add 3333
```

## `/super readonly remove` 命令

### `/super readonly remove` - CHAT

**完整格式**：`/super readonly remove 群号`

**所需权限组**：`super`

将 `群号` 从只读名单移除，群号为必填正整数；仅私聊可用。

解除后按原身份组和提醒规则处理后续命令及发送；不会补发已经跳过的旧提醒，不会重建任务或改变角色名单。更改持久化并记录审计，在当前私聊返回确认。

```text
/super readonly remove 3333
```
