# 全局群 AI 对话管理 命令组

[命令目录](../README.md) · [群 AI 对话](README.md) · [Super 管理](../super/README.md)

本组涉及以下身份组：

- `super`

`/super group-discuss help` 与 `/super help group-discuss` 发送同一 JPEG，均须全局 super。

## `/super group-discuss help` 命令

### `/super group-discuss help` - CHAT

**完整格式**：`/super group-discuss help`

**所需权限组**：`super`

发送当前私聊对应的全局群 AI 管理 JPEG，与 `/super help group-discuss` 相同。页面列出启停、角色、群配置和全局约束；实际操作仍按各入口的权限与会话范围执行。

```text
/super group-discuss help
```

### `/super group-discuss help` - GROUP

**完整格式**：`/super group-discuss help`

**所需权限组**：`super`

发送当前群聊对应的全局群 AI 管理 JPEG，与 `/super help group-discuss` 相同。页面列出启停、角色、群配置和全局约束；实际操作仍按各入口的权限与会话范围执行。

```text
/super group-discuss help
```

## `/super group-discuss enable` 命令

### `/super group-discuss enable` - CHAT

**完整格式**：`/super group-discuss enable GROUP USER`

**所需权限组**：全局 `super`

启用并增加群 discuss super。

```text
/super group-discuss enable GROUP USER
```

### `/super group-discuss enable` - GROUP

**完整格式**：`/super group-discuss enable GROUP USER`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss disable` 命令

### `/super group-discuss disable` - CHAT

**完整格式**：`/super group-discuss disable GROUP`

**所需权限组**：全局 `super`

停用并结束全部活跃会话。

```text
/super group-discuss disable GROUP
```

### `/super group-discuss disable` - GROUP

**完整格式**：`/super group-discuss disable GROUP`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss limits show` 命令

### `/super group-discuss limits show` - CHAT

**完整格式**：`/super group-discuss limits show`

**所需权限组**：全局 `super`

查看全局配置。

```text
/super group-discuss limits show
```

### `/super group-discuss limits show` - GROUP

**完整格式**：`/super group-discuss limits show`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss limits set` 命令

### `/super group-discuss limits set` - CHAT

**完整格式**：`/super group-discuss limits set KEY VALUE`

**所需权限组**：全局 `super`

持久化修改全局配置。

```text
/super group-discuss limits set KEY VALUE
```

### `/super group-discuss limits set` - GROUP

**完整格式**：`/super group-discuss limits set KEY VALUE`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss config show` 命令

### `/super group-discuss config show` - CHAT

**完整格式**：`/super group-discuss config show GROUP [KEY]`

**所需权限组**：全局 `super`

以图片卡片查看任意群配置，展示当前生效值、来源和相关系统约束；指定 KEY 只显示该项，Key 始终脱敏。

```text
/super group-discuss config show GROUP [KEY]
```

### `/super group-discuss config show` - GROUP

**完整格式**：`/super group-discuss config show GROUP [KEY]`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss config set` 命令

### `/super group-discuss config set` - CHAT

**完整格式**：`/super group-discuss config set GROUP KEY VALUE`

**所需权限组**：全局 `super`

修改任意群配置。

```text
/super group-discuss config set GROUP KEY VALUE
```

### `/super group-discuss config set` - GROUP

**完整格式**：`/super group-discuss config set GROUP KEY VALUE`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss config reset` 命令

### `/super group-discuss config reset` - CHAT

**完整格式**：`/super group-discuss config reset GROUP KEY`

**所需权限组**：全局 `super`

重置群设置。

```text
/super group-discuss config reset GROUP KEY
```

### `/super group-discuss config reset` - GROUP

**完整格式**：`/super group-discuss config reset GROUP KEY`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss stats` 命令

### `/super group-discuss stats` - CHAT

**完整格式**：`/super group-discuss stats GROUP [today|YYYY-MM-DD|all]`

**所需权限组**：全局 `super`

统计默认 today。

```text
/super group-discuss stats GROUP [today|YYYY-MM-DD|all]
```

### `/super group-discuss stats` - GROUP

**完整格式**：`/super group-discuss stats GROUP [today|YYYY-MM-DD|all]`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss sessions` 命令

### `/super group-discuss sessions` - CHAT

**完整格式**：`/super group-discuss sessions GROUP`

**所需权限组**：全局 `super`

查看活跃会话。

```text
/super group-discuss sessions GROUP
```

### `/super group-discuss sessions` - GROUP

**完整格式**：`/super group-discuss sessions GROUP`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss end` 命令

### `/super group-discuss end` - CHAT

**完整格式**：`/super group-discuss end GROUP SESSION|all`

**所需权限组**：全局 `super`

强制结束会话。

```text
/super group-discuss end GROUP SESSION|all
```

### `/super group-discuss end` - GROUP

**完整格式**：`/super group-discuss end GROUP SESSION|all`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss usage resolve` 命令

### `/super group-discuss usage resolve` - CHAT

**完整格式**：`/super group-discuss usage resolve GROUP REQUEST TOKENS REASON`

**所需权限组**：全局 `super`

核实供应商账单后核销未知消耗，TOKENS 为该调用总消耗。

```text
/super group-discuss usage resolve GROUP REQUEST TOKENS REASON
```

### `/super group-discuss usage resolve` - GROUP

**完整格式**：`/super group-discuss usage resolve GROUP REQUEST TOKENS REASON`

**所需权限组**：全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/super group-discuss super add` 命令

### `/super group-discuss super add` - CHAT

**完整格式**：`/super group-discuss super add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss super add USER [GROUP]
```

### `/super group-discuss super add` - GROUP

**完整格式**：`/super group-discuss super add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss super add USER [GROUP]
```

## `/super group-discuss super remove` 命令

### `/super group-discuss super remove` - CHAT

**完整格式**：`/super group-discuss super remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss super remove USER [GROUP]
```

### `/super group-discuss super remove` - GROUP

**完整格式**：`/super group-discuss super remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss super remove USER [GROUP]
```

## `/super group-discuss super list` 命令

### `/super group-discuss super list` - CHAT

**完整格式**：`/super group-discuss super list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss super list [GROUP]
```

### `/super group-discuss super list` - GROUP

**完整格式**：`/super group-discuss super list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss super list [GROUP]
```

## `/super group-discuss admin add` 命令

### `/super group-discuss admin add` - CHAT

**完整格式**：`/super group-discuss admin add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss admin add USER [GROUP]
```

### `/super group-discuss admin add` - GROUP

**完整格式**：`/super group-discuss admin add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss admin add USER [GROUP]
```

## `/super group-discuss admin remove` 命令

### `/super group-discuss admin remove` - CHAT

**完整格式**：`/super group-discuss admin remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss admin remove USER [GROUP]
```

### `/super group-discuss admin remove` - GROUP

**完整格式**：`/super group-discuss admin remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss admin remove USER [GROUP]
```

## `/super group-discuss admin list` 命令

### `/super group-discuss admin list` - CHAT

**完整格式**：`/super group-discuss admin list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss admin list [GROUP]
```

### `/super group-discuss admin list` - GROUP

**完整格式**：`/super group-discuss admin list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss admin list [GROUP]
```

## `/super group-discuss user add` 命令

### `/super group-discuss user add` - CHAT

**完整格式**：`/super group-discuss user add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss user add USER [GROUP]
```

### `/super group-discuss user add` - GROUP

**完整格式**：`/super group-discuss user add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss user add USER [GROUP]
```

## `/super group-discuss user remove` 命令

### `/super group-discuss user remove` - CHAT

**完整格式**：`/super group-discuss user remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss user remove USER [GROUP]
```

### `/super group-discuss user remove` - GROUP

**完整格式**：`/super group-discuss user remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss user remove USER [GROUP]
```

## `/super group-discuss user list` 命令

### `/super group-discuss user list` - CHAT

**完整格式**：`/super group-discuss user list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss user list [GROUP]
```

### `/super group-discuss user list` - GROUP

**完整格式**：`/super group-discuss user list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss user list [GROUP]
```

## `/super group-discuss blacklist add` 命令

### `/super group-discuss blacklist add` - CHAT

**完整格式**：`/super group-discuss blacklist add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss blacklist add USER [GROUP]
```

### `/super group-discuss blacklist add` - GROUP

**完整格式**：`/super group-discuss blacklist add USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss blacklist add USER [GROUP]
```

## `/super group-discuss blacklist remove` 命令

### `/super group-discuss blacklist remove` - CHAT

**完整格式**：`/super group-discuss blacklist remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss blacklist remove USER [GROUP]
```

### `/super group-discuss blacklist remove` - GROUP

**完整格式**：`/super group-discuss blacklist remove USER [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss blacklist remove USER [GROUP]
```

## `/super group-discuss blacklist list` 命令

### `/super group-discuss blacklist list` - CHAT

**完整格式**：`/super group-discuss blacklist list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

```text
/super group-discuss blacklist list [GROUP]
```

### `/super group-discuss blacklist list` - GROUP

**完整格式**：`/super group-discuss blacklist list [GROUP]`

**所需权限组**：全局 `super`

操作本群直接身份名单；私聊须填 GROUP。super/admin/user 与 `/super role` 共用授权数据，黑名单仍属于准入策略。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/super group-discuss blacklist list [GROUP]
```
