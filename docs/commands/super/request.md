# Super 申请审批 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：查询、同意和拒绝申请。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super request list` 命令

### `/super request list` - CHAT

**完整格式**：`/super request list [pending|processing|approved|denied|failed|uncertain|all] [--page 页码]`

**所需权限组**：`super`

列出当前机器人收到的好友申请、加群申请及邀请。

### `/super request list` - GROUP

**完整格式**：`/super request list [pending|processing|approved|denied|failed|uncertain|all] [--page 页码]`

**所需权限组**：`super`

须先真实 @机器人。列出当前机器人收到的好友申请、加群申请及邀请。

## `/super request approve` 命令

### `/super request approve` - CHAT

**完整格式**：`/super request approve 编号[,编号]|all`

**所需权限组**：`super`

同意指定待处理申请；all 仅处理 pending。

### `/super request approve` - GROUP

**完整格式**：`/super request approve 编号[,编号]|all`

**所需权限组**：`super`

须先真实 @机器人。同意指定待处理申请；all 仅处理 pending。

## `/super request deny` 命令

### `/super request deny` - CHAT

**完整格式**：`/super request deny 编号[,编号]|all`

**所需权限组**：`super`

拒绝指定待处理申请；all 仅处理 pending。

### `/super request deny` - GROUP

**完整格式**：`/super request deny 编号[,编号]|all`

**所需权限组**：`super`

须先真实 @机器人。拒绝指定待处理申请；all 仅处理 pending。

## 使用规则与示例

OneBot 上报 `request.friend` 或 `request.group`（`add`/`invite`）时，插件保存唯一编号并私聊 Super，展示申请/邀请人、群、时间、附言和处理命令；不调用 AI，不自动同意。

```text
/super request list
/super request list all --page 2
/super request deny 123
/super request deny all
/super request approve 123
/super request approve all
```

- 默认列出当前机器人的 `pending`；可筛选 `approved`、`denied`、`failed`、`uncertain`、`processing`、`all`。
- 同意/拒绝支持逗号分隔多个编号；`all` 只处理调用时已有的 pending，不包含后续新到的申请。
- 编号持久化，重复事件去重；原始 OneBot flag 仅存于数据库并用于接口调用，不展示到列表。
- 审批逐项调用 `set_friend_add_request` 或 `set_group_add_request`。已处理项不会重复调用；结果不确定不自动重试，插件在处理期间重启也标记为 uncertain。
- 群申请能否审批由 QQ 账号实际权限决定；普通账号能收到并处理的范围由 NapCat/OneBot 上报能力决定。失效申请或接口拒绝会记录失败，完整错误仅发给 Super。
- 插件只接收启用后的事件，不拉取启用前的申请，也不会阻止其他插件或 QQ 客户端处理同一申请。
