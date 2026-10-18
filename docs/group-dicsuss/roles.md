# discuss 身份

继承关系：`group.discuss.super → group.discuss.admin → group.discuss.user`。

全局 super 管理全部群并始终拥有有效 user 身份。群 discuss super 可任免本群 discuss admin；群 admin 管理本群配置、user 名单、会话和统计。群 super 的任免与功能启停仅限全局 super。

普通用户准入模式由 admin 私聊设置：

| 模式 | 规则 |
| --- | --- |
| whitelist | 本群成员且在 user 白名单中，初始模式 |
| all | 本群所有成员 |
| blacklist | 本群成员且不在黑名单中 |

两个名单独立保存，切换模式不清空名单。admin/super 继承 user，黑名单和移除 user 直接授权不覆盖继承权限；撤销管理身份后重新按剩余身份和模式计算。

现有全局 admin、group.admin、QQ 原生管理员身份均不自动授予 discuss 权限。discuss 身份独立保存，通过本功能命令查看和管理。

无 user 权限的普通触发静默忽略；管理命令独立鉴权。功能启用、预算、Readonly 和工具限制仍约束正常 AI 对话。
