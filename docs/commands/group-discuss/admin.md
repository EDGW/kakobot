# 群 AI 对话管理 命令组

[命令目录](../README.md) · [群 AI 对话](README.md) · [Super 管理](../super/README.md)

本组涉及以下身份组：

- `group.discuss.super`
- `group.discuss.admin`
- `super`

admin 与群 super 共用本页，命令权限分别标注。`/group-discuss admin help`、`/group-discuss super help`、`/help group-discuss-admin`、`/help group-discuss-super` 发送同一位置的帮助卡片。

## `/group-discuss admin help` 命令

### `/group-discuss admin help` - CHAT

**完整格式**：`/group-discuss admin help`

**所需权限组**：无；所有用户可查看帮助。

发送当前私聊对应的群管理 JPEG，与 `/group-discuss super help`、`/help group-discuss-admin` 为同一页面。各管理命令按下文所需权限执行；查看帮助不授予管理身份。

```text
/group-discuss admin help
```

### `/group-discuss admin help` - GROUP

**完整格式**：`/group-discuss admin help`

**所需权限组**：无；所有用户可查看帮助。

发送当前群聊对应的群管理 JPEG，与 `/group-discuss super help`、`/help group-discuss-admin` 为同一页面。各管理命令按下文所需权限执行；查看帮助不授予管理身份。

```text
/group-discuss admin help
```

## `/group-discuss super help` 命令

### `/group-discuss super help` - CHAT

**完整格式**：`/group-discuss super help`

**所需权限组**：无；所有用户可查看帮助。

发送当前私聊对应的群管理 JPEG，与 `/group-discuss admin help`、`/help group-discuss-admin` 为同一页面。各管理命令按下文所需权限执行；查看帮助不授予管理身份。

```text
/group-discuss super help
```

### `/group-discuss super help` - GROUP

**完整格式**：`/group-discuss super help`

**所需权限组**：无；所有用户可查看帮助。

发送当前群聊对应的群管理 JPEG，与 `/group-discuss admin help`、`/help group-discuss-admin` 为同一页面。各管理命令按下文所需权限执行；查看帮助不授予管理身份。

```text
/group-discuss super help
```

## `/group-discuss admin config show` 命令

### `/group-discuss admin config show` - CHAT

**完整格式**：`/group-discuss admin config show GROUP [KEY]`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

发送配置卡片图片，按用途展示生效值、来源和系统约束；存储值受限时同时列出。指定 KEY 只展示该项，Key 仅展示脱敏值。

```text
/group-discuss admin config show GROUP [KEY]
```

### `/group-discuss admin config show` - GROUP

**完整格式**：`/group-discuss admin config show GROUP [KEY]`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin config set` 命令

### `/group-discuss admin config set` - CHAT

**完整格式**：`/group-discuss admin config set GROUP KEY VALUE`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

设置本群配置，值受系统上限和允许集合约束。

```text
/group-discuss admin config set GROUP KEY VALUE
```

### `/group-discuss admin config set` - GROUP

**完整格式**：`/group-discuss admin config set GROUP KEY VALUE`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin config reset` 命令

### `/group-discuss admin config reset` - CHAT

**完整格式**：`/group-discuss admin config reset GROUP KEY`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

恢复系统默认；api_key 清除，历史用量不重置。

```text
/group-discuss admin config reset GROUP KEY
```

### `/group-discuss admin config reset` - GROUP

**完整格式**：`/group-discuss admin config reset GROUP KEY`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin stats` 命令

### `/group-discuss admin stats` - CHAT

**完整格式**：`/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

查看本群用量、预算和工具统计，默认 today。

```text
/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]
```

### `/group-discuss admin stats` - GROUP

**完整格式**：`/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin sessions` 命令

### `/group-discuss admin sessions` - CHAT

**完整格式**：`/group-discuss admin sessions GROUP`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

查看本群活跃会话。

```text
/group-discuss admin sessions GROUP
```

### `/group-discuss admin sessions` - GROUP

**完整格式**：`/group-discuss admin sessions GROUP`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin end` 命令

### `/group-discuss admin end` - CHAT

**完整格式**：`/group-discuss admin end GROUP SESSION|all`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

结束指定或全部会话，尝试取消在途请求，仍保留已发生或未知消耗。

```text
/group-discuss admin end GROUP SESSION|all
```

### `/group-discuss admin end` - GROUP

**完整格式**：`/group-discuss admin end GROUP SESSION|all`

**所需权限组**：`group.discuss.admin`（含群 super 继承）或全局 `super`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss admin user add` 命令

### `/group-discuss admin user add` - CHAT

**完整格式**：`/group-discuss admin user add USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin user add 10003 123456
```

### `/group-discuss admin user add` - GROUP

**完整格式**：`/group-discuss admin user add USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin user add 10003 123456
```

## `/group-discuss admin user remove` 命令

### `/group-discuss admin user remove` - CHAT

**完整格式**：`/group-discuss admin user remove USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin user remove 10003 123456
```

### `/group-discuss admin user remove` - GROUP

**完整格式**：`/group-discuss admin user remove USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin user remove 10003 123456
```

## `/group-discuss admin user list` 命令

### `/group-discuss admin user list` - CHAT

**完整格式**：`/group-discuss admin user list [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin user list 123456
```

### `/group-discuss admin user list` - GROUP

**完整格式**：`/group-discuss admin user list [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin user list 123456
```

## `/group-discuss admin user show` 命令

### `/group-discuss admin user show` - CHAT

**完整格式**：`/group-discuss admin user show USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin user show 10003 123456
```

### `/group-discuss admin user show` - GROUP

**完整格式**：`/group-discuss admin user show USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin user show 10003 123456
```

## `/group-discuss admin blacklist add` 命令

### `/group-discuss admin blacklist add` - CHAT

**完整格式**：`/group-discuss admin blacklist add USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin blacklist add 10003 123456
```

### `/group-discuss admin blacklist add` - GROUP

**完整格式**：`/group-discuss admin blacklist add USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin blacklist add 10003 123456
```

## `/group-discuss admin blacklist remove` 命令

### `/group-discuss admin blacklist remove` - CHAT

**完整格式**：`/group-discuss admin blacklist remove USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin blacklist remove 10003 123456
```

### `/group-discuss admin blacklist remove` - GROUP

**完整格式**：`/group-discuss admin blacklist remove USER [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin blacklist remove 10003 123456
```

## `/group-discuss admin blacklist list` 命令

### `/group-discuss admin blacklist list` - CHAT

**完整格式**：`/group-discuss admin blacklist list [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

```text
/group-discuss admin blacklist list 123456
```

### `/group-discuss admin blacklist list` - GROUP

**完整格式**：`/group-discuss admin blacklist list [GROUP]`

**所需权限组**：`group.discuss.admin` 或继承身份

user 操作白名单；blacklist 操作独立黑名单。私聊必须填 GROUP；名单操作不撤销继承权限。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss admin blacklist list 123456
```

## `/group-discuss super admin add` 命令

### `/group-discuss super admin add` - CHAT

**完整格式**：`/group-discuss super admin add USER [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

```text
/group-discuss super admin add 10002 123456
```

### `/group-discuss super admin add` - GROUP

**完整格式**：`/group-discuss super admin add USER [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss super admin add 10002 123456
```

## `/group-discuss super admin remove` 命令

### `/group-discuss super admin remove` - CHAT

**完整格式**：`/group-discuss super admin remove USER [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

```text
/group-discuss super admin remove 10002 123456
```

### `/group-discuss super admin remove` - GROUP

**完整格式**：`/group-discuss super admin remove USER [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss super admin remove 10002 123456
```

## `/group-discuss super admin list` 命令

### `/group-discuss super admin list` - CHAT

**完整格式**：`/group-discuss super admin list [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

```text
/group-discuss super admin list 123456
```

### `/group-discuss super admin list` - GROUP

**完整格式**：`/group-discuss super admin list [GROUP]`

**所需权限组**：`group.discuss.super` 或全局 `super`

任免或查看本群 admin 直接授权。群 admin 不能执行。移除直接 admin 不撤销仍存在的群 super 继承。私聊必须指定 GROUP。

群内需 @ 机器人；身份组管理可省略 GROUP 表示本群，禁止跨群。

```text
/group-discuss super admin list 123456
```
