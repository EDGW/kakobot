# /super group-discuss

仅全局 super 可使用。配置、统计、会话和启停命令仅限私聊；身份命令可以私聊或群聊，群聊需 @ 机器人，只能管理本群。

## 私聊命令

- `enable GROUP USER`：开启本群并为 USER 增加 group.discuss.super，不清除已有授权。
- `disable GROUP`：停用并结束本群全部会话，保留配置和账本。
- `config show GROUP [KEY]`、`config set GROUP KEY VALUE`、`config reset GROUP KEY`：查看及修改任意群配置。
- `limits show`、`limits set KEY VALUE`：管理系统默认和上限。
- `stats GROUP [today|YYYY-MM-DD|all]`：统计，默认 today。
- `sessions GROUP`：活跃会话。
- `end GROUP SESSION|all`：强制结束。
- `usage resolve GROUP REQUEST TOKENS REASON`：核实供应商用量后人工核销未知请求，TOKENS 是该调用确认的总消耗，不是增量；保留原 usage 和审计。

以上命令统一加 `/super group-discuss` 前缀。没有有效凭据或允许模型时，即使启用也不能付费调用。

## 身份管理

```text
/super group-discuss super add USER GROUP
/super group-discuss super remove USER GROUP
/super group-discuss super list GROUP
/super group-discuss admin add USER GROUP
/super group-discuss admin remove USER GROUP
/super group-discuss admin list GROUP
```

也可使用该入口的 `user`、`blacklist` add/remove/list/show 子命令。群聊省略 GROUP 表示本群；私聊必须明确群号。

全局 super 还可使用群 super/admin 的全部命令操作任意群。群功能停用、预算耗尽、群名单和角色变更不能撤销其管理权。群级设置不能突破系统 config 上限；全局 super 可修改上限。
