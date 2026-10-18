# 群 AI 对话帮助与会话 命令组

[命令目录](../README.md) · [群 AI 对话](README.md) · [Super 管理](../super/README.md)

本组涉及以下身份组：

- 无：查看帮助和本人身份。
- `group.discuss.user`：发起对话，查看和结束自己创建的会话。
- `group.discuss.admin`：继承 user；群 super 继承 admin。

真实 @ 机器人新建会话，回复机器人的 discuss 回答继续原会话。无有效 user 权限时静默忽略。会话超限按创建时间淘汰，会话预算不足自动结束，每日额度不足暂停；上下文压缩不清零消耗。每轮附输入、输出、缓存命中、工具次数及搜索来源。

## `/group-discuss help` 命令

### `/group-discuss help` - CHAT

**完整格式**：`/group-discuss help [help|admin|roles|tools|configuration|statistics]`

**所需权限组**：无；所有用户可用。

发送当前私聊对应的群 AI 帮助 JPEG。省略主题时发送本页；指定主题时发送该主题完整文档图片。

| 主题 | 用法 | 内容 |
| --- | --- | --- |
| help | `/group-discuss help` 或 `/group-discuss help help` | 当前帮助页和自己的会话管理 |
| admin | `/group-discuss help admin` | 群 admin 与群 super 共用管理帮助 |
| roles | `/group-discuss help roles` | 角色继承、统一身份管理与用户准入 |
| tools | `/group-discuss help tools` | 工具权限、联网能力与费用归属 |
| configuration | `/group-discuss help configuration` | 群配置、默认值与系统约束 |
| statistics | `/group-discuss help statistics` | 预算、用量、压缩与统计 |

`/help group-discuss` 发送本页；其他主题也可通过 `/help group-discuss-主题` 查看。`/group-discuss admin help` 与 `/group-discuss super help` 共用 admin 管理卡片，group-super 是 admin 主题别名；全局管理帮助使用 `/super help group-discuss`，须全局 super。

图片按 CHAT/GROUP 选择，不按个人身份组裁剪；能查看帮助不代表拥有执行权限。只接受一个主题，不支持继续追加子命令。不存在的主题返回提示，缺失或损坏的图片提示重新构建，不回退文字帮助。图片只发送到当前会话。

```text
/group-discuss help
/group-discuss help admin
/group-discuss help tools
```

### `/group-discuss help` - GROUP

**完整格式**：`/group-discuss help [help|admin|roles|tools]`

**所需权限组**：无；所有用户可用。

发送当前群聊对应的群 AI 帮助 JPEG。省略主题时发送本页；指定主题时发送该主题完整文档图片。

| 主题 | 用法 | 内容 |
| --- | --- | --- |
| help | `/group-discuss help` 或 `/group-discuss help help` | 当前帮助页和自己的会话管理 |
| admin | `/group-discuss help admin` | 群 admin 与群 super 共用管理帮助 |
| roles | `/group-discuss help roles` | 角色继承、统一身份管理与用户准入 |
| tools | `/group-discuss help tools` | 工具权限、联网能力与费用归属 |

`/help group-discuss` 发送本页；其他主题也可通过 `/help group-discuss-主题` 查看。`/group-discuss admin help` 与 `/group-discuss super help` 共用 admin 管理卡片，group-super 是 admin 主题别名；全局管理帮助使用 `/super help group-discuss`，须全局 super。

图片按 CHAT/GROUP 选择，不按个人身份组裁剪；能查看帮助不代表拥有执行权限。只接受一个主题，不支持继续追加子命令。不存在的主题返回提示，缺失或损坏的图片提示重新构建，不回退文字帮助。图片只发送到当前会话。

群内需 @ 机器人。配置与统计专题请私聊查看；`/help group-discuss-configuration` 和 `/help group-discuss-statistics` 可查看静态说明，实际配置与统计操作仅限私聊。

```text
/group-discuss help
/group-discuss help admin
/group-discuss help tools
```

## `/group-discuss role` 命令

### `/group-discuss role` - CHAT

**完整格式**：`/group-discuss role GROUP`

**所需权限组**：无；仅查看本人。

查看本人本群 discuss 身份及 user 准入。私聊必须指定群号；也可通过 `/role` 查看统一角色与来源。

```text
/group-discuss role 123456
```

### `/group-discuss role` - GROUP

**完整格式**：`/group-discuss role`

**所需权限组**：无；仅查看本人。

查看本人当前群的 discuss 身份及 user 准入，也可通过 `/role` 查看统一角色与来源。

群内需 @ 机器人；只查看当前群，不接受额外群号。

```text
/group-discuss role
```

## `/group-discuss sessions` 命令

### `/group-discuss sessions` - CHAT

**完整格式**：`/group-discuss sessions GROUP`

**所需权限组**：有效 `group.discuss.user`

仅列出自己创建的活跃会话。

```text
/group-discuss sessions 123456
```

### `/group-discuss sessions` - GROUP

**完整格式**：`/group-discuss sessions GROUP`

**所需权限组**：有效 `group.discuss.user`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss end` 命令

### `/group-discuss end` - CHAT

**完整格式**：`/group-discuss end GROUP SESSION`

**所需权限组**：有效 `group.discuss.user`

只能结束自己创建的会话，不能使用 all。

```text
/group-discuss end 123456 SESSION
```

### `/group-discuss end` - GROUP

**完整格式**：`/group-discuss end GROUP SESSION`

**所需权限组**：有效 `group.discuss.user`

当前位置不可执行；请私聊机器人并明确目标群号。
