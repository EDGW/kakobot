# Super 命令目录

[命令目录](../README.md) · [返回 README](../../../README.md) · [配置与存储](../../configuration.md)

只有配置项 `super_user` 指定的账号可调用。`/super` 或 `/super help` 发送当前 CHAT/GROUP 的 Super help 图片；`/super help 功能组` 发送该组整页图片，例如 `/super help announce`。非 Super 无法使用 Super 帮助入口。

| 功能 | 文档 |
| --- | --- |
| 管理帮助 | [help](help.md) |
| 身份组授权、来源与批量重置 | [role](role.md) |
| 跨会话 DDL 查询、修改和取消 | [ddl](ddl.md) |
| 待发提醒任务 | [schedule](schedule.md) |
| 好友申请、加群申请、入群邀请 | [request](request.md) |
| 用量和费用 | [cost](cost.md) |
| 更新及自定义广播 | [announce](announce.md) |
| 只读群管理 | [readonly](readonly.md) |

## 通用约定

- 涉及群身份组与 DDL 管理时只能指定本群；跨会话 DDL 管理请私聊。schedule、cost 支持群内查询全部或指定对象，结果返回当前会话。
- DDL、提醒、费用和申请只涉及当前连接的平台与机器人账号，不切换其他账号。
- QQ、身份组、任务引用用英文逗号批量指定，一般每个列表最多100项；每条 DDL 最多20位通知对象。
- 身份组和 DDL 修改先完整校验、一次保存；`--dry-run` 只预览，不保存也不发送通知。参数含空格时使用英文双引号。
- Readonly 独立生效；私聊也不能通过管理命令修改只读群 DDL，但可以查看。
- 权限、DDL 与申请处理记录操作者、时间和前后内容。外部接口操作无法回滚，申请批量审批逐项汇报。

## 兼容入口

旧 Super 专用 `/role list/add/remove/clear/reset/group-admin`、`/cost`、`/announce`、`/readonly add/remove` 在过渡版本中转发至对应 Super 命令，帮助只展示新入口。不存在独立 `/request` 命令。

`/send` 和 `/readonly list` 继续向全局 admin 开放；详见普通命令目录。
