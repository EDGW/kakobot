# /group-discuss help

群 AI 对话仅响应 @ 机器人或回复机器人消息；每次检查本群 user 权限。@ 开新会话，回复 discuss 回答继续原会话。回答末尾展示本轮输入/输出 tokens、缓存命中与实际工具调用次数。

## 帮助

`/group-discuss help [roles|tools|configuration|statistics]`：查看独立功能文档；配置及统计帮助请私聊查看。

`/group-discuss admin help`、`/group-discuss super help`：群管理员及群 super 的命令说明。

全局 super 使用 `/super group-discuss help` 管理任意群。

## 普通用户命令

- `/group-discuss role GROUP`：私聊查看本人在目标群的身份、准入模式和有效 user 状态。
- `/group-discuss role`：群内查看本人本群身份，需 @ 机器人。
- `/group-discuss sessions GROUP`：私聊查看自己创建的活跃会话。
- `/group-discuss end GROUP SESSION`：私聊结束自己创建的会话。

会话数超限关闭最早创建的旧会话；会话预算不足自动结束。每日额度耗尽暂停调用，次日恢复；压缩上下文不清零累计 token 消耗。当前没有空闲超时自动结束规则。
