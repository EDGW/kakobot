# KakoBot

AstrBot 的 OneBot v11 QQ 插件，支持群聊和个人 DDL 提醒、私聊消息及合并转发自动分析、聊天总结，以及 Super 管理。

## 安装

1. 从 [Releases](https://github.com/EDGW/kakobot/releases) 下载插件 ZIP，在 AstrBot 插件管理中安装。
2. 通过 NapCat 等 OneBot v11 实现连接 QQ，配置 `super_user` 为自己的 QQ 号。
3. 需要 AI 功能时，填写 `api_address`、`api_key` 和 `model_name`；服务需支持 Responses API。
4. Super 私聊机器人，授权用户或群成员：

```text
/super role add 123456789 autoanalysis
/super role add 123456789 3333.ddl
```

第一条允许该用户私聊自动分析及使用个人 DDL、总结；第二条允许其在群 3333 创建 DDL。群身份组与 QQ 原生管理员无关。

升级时保留插件数据目录，并先停止旧插件。

## 最基本的用法

以下功能按身份组授权，`/help` 发送当前会话的图片帮助，`/help ddl` 等查询对应功能文档；具体权限见图片内的说明。

| 用法 | 作用 |
| --- | --- |
| `/help`、`/role` | 查看图片帮助、自己的身份组 |
| `/changelog`、`/version` | 查看更新日志图片、当前安装版本；所有用户可用 |
| `/ddl add 明天18点交物理作业，提前3小时提醒` | 让 AI 创建一条 DDL |
| `/ddl list`、`/ddl view` | 查看详细列表、时间卡片 |
| `/ddl show 3`、`/ddl remove 3` | 查看或取消编号为3的 DDL 通知 |
| `/summary text 内容` | 总结文字 |
| `/announce-reject on` | 拒收广播；`off` 恢复，不影响 DDL 提醒 |

有 `autoanalysis` 权限时，可以直接私聊发送文字、引用或合并聊天记录来添加个人 DDL；修改任务时明确编号和要求，例如“把 DDL #3 的标题改成提交物理作业”。取消请使用 `/ddl remove 编号`。

Super 使用 `/super help` 管理身份组、各用户和各群的 DDL、好友申请与群申请、费用、广播和只读群。

## 详细文档

- [普通命令与 DDL](docs/commands/README.md)：创建、提醒规则、自动分析、总结。
- [Super 管理](docs/commands/super/README.md)：批量身份组、跨会话 DDL、申请审批与其他管理命令。
- [配置与升级](docs/configuration.md)：配置项、存储、日志和运行约定。
- [开发与打包](docs/development.md)：代码结构、本地检查与 ZIP 构建。

时间默认使用北京时间。各群和各用户的个人任务独立；Readonly 在身份组之外拦截，Super 也不能绕过。
