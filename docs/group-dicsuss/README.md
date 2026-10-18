# 群 AI 对话

独立的 `/group-discuss` 功能，使用 DeepSeek Responses 和 Pydantic AI。所有群初始关闭；已有 group.admin、全局 admin 或 QQ 群管理员不会自动获得本功能管理权限。

群内只响应真实 @ 机器人或回复机器人消息。单独 @ 新建会话，回复 discuss 回答延续原会话，其他有 user 权限的用户也能参与。普通群聊天不进入上下文，已结束会话不能复活。

- [帮助和普通用户命令](help.md)
- [群配置及全局约束](configuration.md)
- [角色与 user 准入](roles.md)
- [全局 super 管理](super.md)
- [群 discuss super](group-super.md)
- [群 discuss admin](admin.md)
- [工具](tools.md)
- [预算与统计](statistics.md)

配置、统计及会话管理只能私聊并明确群号；身份组管理可以私聊或群聊，群聊需 @ 机器人且只能管理本群。

全局 super 拥有最终管理权，可接管任何群；仍遵守私聊管理位置规则和既有 Readonly 机制。功能关闭、名单或额度不能阻断其私聊管理命令。
