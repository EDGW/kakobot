# /group-discuss admin

需要目标群 group.discuss.admin、继承该权限的群 discuss super，或全局 super。

## 仅限私聊

```text
/group-discuss admin config show GROUP [KEY]
/group-discuss admin config set GROUP KEY VALUE
/group-discuss admin config reset GROUP KEY
/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]
/group-discuss admin sessions GROUP
/group-discuss admin end GROUP SESSION|all
```

config 支持会话数、token 预算、user_mode、独立 api_key、DeepSeek 模型、思考强度、群系统提示词 system_prompt、上下文参数及工具开关和次数上限。api_key 永远不回显原文，设置和撤销不改变历史用量。

## 私聊或群聊的身份管理

```text
/group-discuss admin user add USER GROUP
/group-discuss admin user remove USER GROUP
/group-discuss admin user list GROUP
/group-discuss admin user show USER GROUP
/group-discuss admin blacklist add USER GROUP
/group-discuss admin blacklist remove USER GROUP
/group-discuss admin blacklist list GROUP
```

群聊需 @ 机器人，GROUP 可省略表示本群；私聊必须明确群号。user 操作维护白名单，blacklist 维护独立黑名单。user_mode 是具体配置，必须私聊修改。

admin 自动继承 user；黑名单不能撤销继承权限。群 admin 不能任免 admin、super，不能启停功能或提高系统上限。
