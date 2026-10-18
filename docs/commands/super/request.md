# Super 申请审批 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：查询、同意和拒绝申请。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super request list` 命令

### `/super request list` - CHAT

**完整格式**：`/super request list [pending|processing|approved|denied|failed|uncertain|all] [--page 页码]`

**所需权限组**：`super`

查看当前平台与机器人账号收到的好友申请、加群申请及入群邀请。省略状态时只列出 pending，不会拉取插件启用前的历史申请。

- `pending`：等待处理。
- `processing`：接口处理进行中。
- `approved`、`denied`：已同意或拒绝。
- `failed`：处理失败。
- `uncertain`：无法确认接口结果，或处理期间插件重启。
- `all`：不按状态筛选。
- `--page`：正整数，默认1，每页20项，越界会提示。

每项显示持久化编号、申请/邀请人、群、收到时间、附言和处理说明；接口内部 flag 不展示。OneBot 事件重复上报会去重，收到新申请时私聊通知 Super，不自动同意，也不调用 AI。

```text
/super request list
/super request list all --page 2
/super request list uncertain
```

### `/super request list` - GROUP

**完整格式**：`/super request list [pending|processing|approved|denied|failed|uncertain|all] [--page 页码]`

**所需权限组**：`super`

查看当前平台与机器人账号收到的好友申请、加群申请及入群邀请。省略状态时只列出 pending，不会拉取插件启用前的历史申请。

- `pending`：等待处理。
- `processing`：接口处理进行中。
- `approved`、`denied`：已同意或拒绝。
- `failed`：处理失败。
- `uncertain`：无法确认接口结果，或处理期间插件重启。
- `all`：不按状态筛选。
- `--page`：正整数，默认1，每页20项，越界会提示。

每项显示持久化编号、申请/邀请人、群、收到时间、附言和处理说明；接口内部 flag 不展示。OneBot 事件重复上报会去重，收到新申请时私聊通知 Super，不自动同意，也不调用 AI。

```text
/super request list
/super request list all --page 2
/super request list uncertain
```

## `/super request approve` 命令

### `/super request approve` - CHAT

**完整格式**：`/super request approve 编号[,编号]|all`

**所需权限组**：`super`

同意明确指定的待处理申请，可处理好友申请、加群申请或入群邀请。

- `编号[,编号]`：按 list 显示的编号选择，多项用英文逗号分隔，最多100项。所有编号都必须属于当前平台与机器人账号，且状态为 pending；任一编号无效或已处理时整批不执行。
- `all`：只处理执行命令时已有的 pending 快照，不包含之后新到的申请。

逐项调用 QQ 接口并返回成功、失败或结果不确定的统计；某项接口失败不会回滚已经完成的项。已处理或 uncertain 项不重复调用、不自动重试；处理期间重启的项记为 uncertain。Super 权限失效会停止后续处理。

群申请能否处理仍取决于 QQ 账号实际权限及 OneBot 上报能力；其他插件或客户端处理同一申请可能使接口拒绝，错误会记录并报告给 Super。

```text
/super request approve 123,124
/super request approve all
```

### `/super request approve` - GROUP

**完整格式**：`/super request approve 编号[,编号]|all`

**所需权限组**：`super`

同意明确指定的待处理申请，可处理好友申请、加群申请或入群邀请。

- `编号[,编号]`：按 list 显示的编号选择，多项用英文逗号分隔，最多100项。所有编号都必须属于当前平台与机器人账号，且状态为 pending；任一编号无效或已处理时整批不执行。
- `all`：只处理执行命令时已有的 pending 快照，不包含之后新到的申请。

逐项调用 QQ 接口并返回成功、失败或结果不确定的统计；某项接口失败不会回滚已经完成的项。已处理或 uncertain 项不重复调用、不自动重试；处理期间重启的项记为 uncertain。Super 权限失效会停止后续处理。

群申请能否处理仍取决于 QQ 账号实际权限及 OneBot 上报能力；其他插件或客户端处理同一申请可能使接口拒绝，错误会记录并报告给 Super。

```text
/super request approve 123,124
/super request approve all
```

## `/super request deny` 命令

### `/super request deny` - CHAT

**完整格式**：`/super request deny 编号[,编号]|all`

**所需权限组**：`super`

拒绝明确指定的待处理申请，可处理好友申请、加群申请或入群邀请。

- `编号[,编号]`：按 list 显示的编号选择，多项用英文逗号分隔，最多100项。所有编号都必须属于当前平台与机器人账号，且状态为 pending；任一编号无效或已处理时整批不执行。
- `all`：只处理执行命令时已有的 pending 快照，不包含之后新到的申请。

逐项调用 QQ 接口并返回成功、失败或结果不确定的统计；某项接口失败不会回滚已经完成的项。已处理或 uncertain 项不重复调用、不自动重试；处理期间重启的项记为 uncertain。Super 权限失效会停止后续处理。

群申请能否处理仍取决于 QQ 账号实际权限及 OneBot 上报能力；其他插件或客户端处理同一申请可能使接口拒绝，错误会记录并报告给 Super。

```text
/super request deny 123,124
/super request deny all
```

### `/super request deny` - GROUP

**完整格式**：`/super request deny 编号[,编号]|all`

**所需权限组**：`super`

拒绝明确指定的待处理申请，可处理好友申请、加群申请或入群邀请。

- `编号[,编号]`：按 list 显示的编号选择，多项用英文逗号分隔，最多100项。所有编号都必须属于当前平台与机器人账号，且状态为 pending；任一编号无效或已处理时整批不执行。
- `all`：只处理执行命令时已有的 pending 快照，不包含之后新到的申请。

逐项调用 QQ 接口并返回成功、失败或结果不确定的统计；某项接口失败不会回滚已经完成的项。已处理或 uncertain 项不重复调用、不自动重试；处理期间重启的项记为 uncertain。Super 权限失效会停止后续处理。

群申请能否处理仍取决于 QQ 账号实际权限及 OneBot 上报能力；其他插件或客户端处理同一申请可能使接口拒绝，错误会记录并报告给 Super。

```text
/super request deny 123,124
/super request deny all
```
