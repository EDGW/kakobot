# Super 帮助 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：仅配置 super_user 指定。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super` 命令

### `/super` - CHAT

**完整格式**：`/super`

**所需权限组**：`super`

发送当前私聊对应的 Super help 图片，与不带参数的 `/super help` 完全相同。页面列出 Super 各功能组的图片帮助入口，不生成旧的文字管理列表。

要查看具体组，请执行 `/super help role`、`/super help ddl`、`/super help announce` 等。读取及发送前仍需通过 Super 鉴权，图片发回执行命令的当前会话。

### `/super` - GROUP

**完整格式**：`/super`

**所需权限组**：`super`

发送当前群聊对应的 Super help 图片，与不带参数的 `/super help` 完全相同。页面列出 Super 各功能组的图片帮助入口，不生成旧的文字管理列表。

要查看具体组，请执行 `/super help role`、`/super help ddl`、`/super help announce` 等。读取及发送前仍需通过 Super 鉴权，图片发回执行命令的当前会话。

## `/super help` 命令

### `/super help` - CHAT

**完整格式**：`/super help [help|role|ddl|schedule|request|cost|announce|readonly]`

**所需权限组**：`super`

发送当前私聊对应的 Super 功能组帮助 JPEG。省略功能组时发送本页；指定功能组时发送该组完整文档图片。

| 功能组 | 用法 | 内容 |
| --- | --- | --- |
| help | `/super help` 或 `/super help help` | 当前 Super 帮助页 |
| role | `/super help role` | 身份组授权、来源和重置 |
| ddl | `/super help ddl` | 跨会话任务查询、修改和取消 |
| schedule | `/super help schedule` | 当前机器人全部或指定会话的待发提醒 |
| request | `/super help request` | 好友、加群申请及邀请审批 |
| cost | `/super help cost` | 用量与费用 |
| announce | `/super help announce` | 更新及自定义广播 |
| readonly | `/super help readonly` | 查询和修改只读群 |

功能组名与 Super 命令文档文件名一致，不含扩展名，可带一个开头斜线，大小写不敏感。只接受一个功能组，不再支持 `/super help ddl edit` 这样的子命令筛选；编辑参数请看 `/super help ddl`。

图片按 CHAT/GROUP 选择；只能私聊执行的功能在群聊图片中标注不可用。查询图片不会放宽具体命令的资源范围，例如群内 DDL 管理仍只限本群。非 Super 不能读取或发送这些页面。

不存在的页面返回未找到提示，缺失或损坏的图片提示重新构建；不回退旧文字帮助。发送目标始终为当前会话。

```text
/super help
/super help ddl
/super help announce
```

### `/super help` - GROUP

**完整格式**：`/super help [help|role|ddl|schedule|request|cost|announce|readonly]`

**所需权限组**：`super`

发送当前群聊对应的 Super 功能组帮助 JPEG。省略功能组时发送本页；指定功能组时发送该组完整文档图片。

| 功能组 | 用法 | 内容 |
| --- | --- | --- |
| help | `/super help` 或 `/super help help` | 当前 Super 帮助页 |
| role | `/super help role` | 身份组授权、来源和重置 |
| ddl | `/super help ddl` | 跨会话任务查询、修改和取消 |
| schedule | `/super help schedule` | 当前机器人全部或指定会话的待发提醒 |
| request | `/super help request` | 好友、加群申请及邀请审批 |
| cost | `/super help cost` | 用量与费用 |
| announce | `/super help announce` | 更新及自定义广播 |
| readonly | `/super help readonly` | 查询和修改只读群 |

功能组名与 Super 命令文档文件名一致，不含扩展名，可带一个开头斜线，大小写不敏感。只接受一个功能组，不再支持 `/super help ddl edit` 这样的子命令筛选；编辑参数请看 `/super help ddl`。

图片按 CHAT/GROUP 选择；只能私聊执行的功能在群聊图片中标注不可用。查询图片不会放宽具体命令的资源范围，例如群内 DDL 管理仍只限本群。非 Super 不能读取或发送这些页面。

不存在的页面返回未找到提示，缺失或损坏的图片提示重新构建；不回退旧文字帮助。发送目标始终为当前会话。

```text
/super help
/super help ddl
/super help announce
```
