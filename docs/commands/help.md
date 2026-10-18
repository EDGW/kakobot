# 帮助与问候 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组：

- 无；所有用户可用。

## `/help` 命令

### `/help` - CHAT

**完整格式**：`/help [功能组]`

**所需权限组**：无；所有用户可用。

发送当前私聊对应的帮助 JPEG。省略功能组时发送本页；指定功能组时发送该组的完整文档图片，不再生成原来的文字命令列表。

| 功能组 | 用法 | 内容 |
| --- | --- | --- |
| help | `/help` 或 `/help help` | 当前帮助页 |
| ddl | `/help ddl` | 创建、查看、取消、清空和默认提醒 |
| autoanalysis | `/help autoanalysis` | 私聊消息自动识别与修改 |
| role | `/help role` | 本人身份组与权限来源 |
| summary | `/help summary` | 文字、聊天记录及群历史总结 |
| announce-reject | `/help announce-reject` | 广播接收与拒收 |
| send | `/help send` | 向指定群发送文字 |
| readonly | `/help readonly` | 查询只读群 |
| changelog | `/help changelog` | 查看更新日志命令的说明；`/changelog` 展示日志正文图片 |
| version | `/help version` | 查看版本查询命令的说明；`/version` 返回当前版本号 |

功能组名与普通命令文档文件名一致，不含扩展名。不支持继续追加子命令：`/help ddl add-strict` 不再有效，创建语法请看 `/help ddl`。功能组名可带一个开头斜线，大小写不敏感。

文档按 CHAT/GROUP 区分，不按个人身份组动态删减内容；每个入口在图片中写明所需权限，能查看文档不代表拥有执行权限。未开放当前会话的功能页会显示不可用说明，例如群内查询 autoanalysis。Super 文档须通过 `/super help 功能组` 查询。

不存在的功能组返回未找到提示；图片缺失或损坏时提示重新构建，不回退到旧文字帮助。图片只发送到执行命令的当前会话。

```text
/help
/help ddl
/help summary
```

### `/help` - GROUP

**完整格式**：`/help [功能组]`

**所需权限组**：无；所有用户可用。

发送当前群聊对应的帮助 JPEG。省略功能组时发送本页；指定功能组时发送该组的完整文档图片，不再生成原来的文字命令列表。

| 功能组 | 用法 | 内容 |
| --- | --- | --- |
| help | `/help` 或 `/help help` | 当前帮助页 |
| ddl | `/help ddl` | 创建、查看、取消、清空和默认提醒 |
| autoanalysis | `/help autoanalysis` | 私聊消息自动识别与修改 |
| role | `/help role` | 本人身份组与权限来源 |
| summary | `/help summary` | 文字、聊天记录及群历史总结 |
| announce-reject | `/help announce-reject` | 广播接收与拒收 |
| send | `/help send` | 向指定群发送文字 |
| readonly | `/help readonly` | 查询只读群 |
| changelog | `/help changelog` | 查看更新日志命令的说明；`/changelog` 展示日志正文图片 |
| version | `/help version` | 查看版本查询命令的说明；`/version` 返回当前版本号 |

功能组名与普通命令文档文件名一致，不含扩展名。不支持继续追加子命令：`/help ddl add-strict` 不再有效，创建语法请看 `/help ddl`。功能组名可带一个开头斜线，大小写不敏感。

文档按 CHAT/GROUP 区分，不按个人身份组动态删减内容；每个入口在图片中写明所需权限，能查看文档不代表拥有执行权限。未开放当前会话的功能页会显示不可用说明，例如群内查询 autoanalysis。Super 文档须通过 `/super help 功能组` 查询。

不存在的功能组返回未找到提示；图片缺失或损坏时提示重新构建，不回退到旧文字帮助。图片只发送到执行命令的当前会话。

```text
/help
/help ddl
/help summary
```

## `hello` 命令

### `hello` - GROUP

**完整格式**：`你好`

**所需权限组**：无；所有用户可用。

当消息正文只有“你好”时，回复“好牛魔呢”。带有其他正文时不触发此问候；此入口仅在群聊提供。
