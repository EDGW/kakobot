# /group-discuss super

group.discuss.super 继承本群 admin 和 user 权限，可使用全部 admin 命令。群 super 由全局 super 任免，不能自行增加同级 super。

```text
/group-discuss super admin add USER GROUP
/group-discuss super admin remove USER GROUP
/group-discuss super admin list GROUP
```

身份管理可以私聊或群聊，群聊需 @ 机器人，可省略 GROUP 表示本群，不能跨群。私聊必须提供群号。

remove 只撤销直接 admin 身份；如果该用户仍有群 super 身份，其继承的 admin/user 权限保持有效。

所有本群具体配置、统计及会话管理仍然只能私聊执行。
