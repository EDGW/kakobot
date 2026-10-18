# Super 管理

[返回 README](../README.md) · [普通命令](commands.md) · [配置与存储](configuration.md)

只有配置项 `super_user` 指定的账号可调用。`/super` 或 `/super help` 查看管理帮助，`/super help role`、`/super help ddl`、`/super help request` 查看分类；非 Super 的 `/help` 不展示这些入口、用法和示例。

## 范围与批量约定

- 群内须真实 @机器人；群身份组和 DDL 只能管理当前群。跨会话管理请私聊。
- DDL、费用和申请默认只涉及当前连接的平台与机器人账号，不切换其他账号。
- QQ、身份组、任务引用用英文逗号批量指定；一般每个列表最多100项。通知对象每个任务最多20人。
- 身份组和 DDL 批量修改先完整校验，再一次性保存。`--dry-run` 只预览，不保存、不发送通知。
- 参数含空格时使用英文双引号。Readonly 独立生效，私聊也不能通过管理命令修改只读群的 DDL；允许私聊查看。
- 权限、DDL 与申请处理记录操作者、时间及修改前后内容。外部接口操作无法回滚，申请批量审批逐项汇报。

## 身份组

| 命令 | 行为 |
| --- | --- |
| `/super role show QQ[,QQ] [--page 页码]` | 查询指定人员的全局及群权限与来源，每页20人 |
| `/super role list [ROLE] [--group 群号] [--source direct\|inherited\|everyone] [--page 页码]` | 按身份组、群、直接/继承/全员来源筛选，分页展示 |
| `/super role add QQ[,QQ] ROLE[,ROLE]` | 批量添加直接授权 |
| `/super role remove QQ[,QQ] ROLE[,ROLE]` | 批量移除指定直接授权 |
| `/super role set QQ[,QQ] ROLE[,ROLE] --scope global\|group:群号` | 替换单一范围内的直接授权；该范围之外保持原样 |
| `/super role clear QQ[,QQ] --scope global\|group:群号\|all` | 清空指定范围的直接授权；all 仅私聊可用 |
| `/super role reset [群号[,群号]] [--roles group.ddl,group.summary]` | 清空目标群全部或指定群组的直接持有者；群内默认本群，私聊须指定群 |
| `/super role group-admin on\|off [群号[,群号]]` | on 让所有实际群成员获得 group.admin；off 恢复名单校验 |

所有修改命令均支持 `--dry-run`。群内 `--scope group` 可指本群。

全局组为 `super`、`admin`、`autoanalysis`、`ddl`、`summary`。`super` 可查询，但只能通过配置修改。群内使用 `group.admin`、`group.ddl`、`group.summary`；私聊使用 `3333.admin`、`3333.ddl`、`3333.summary`。

`remove/clear/reset` 只改变直接授权，不屏蔽继承权限。`reset` 不关闭全员模式，不改全局授权，也不取消既有任务。

```text
/super role add 111,222 ddl,summary
/super role add 111,222 3333.ddl,4444.summary
/super role list autoanalysis --source inherited
/super role list --group 3333 --page 2
/super role set 111,222 ddl --scope global --dry-run
/super role clear 111,222 --scope group:3333
/super role reset 3333,4444 --roles group.ddl
/super role group-admin off 3333,4444
```

## 跨会话 DDL 查询

对象写作 `user:QQ`（个人任务）、`group:群号`（群任务）或 `this`（当前会话）。完整编号如 `user:111#3`、`group:3333#3`；只有裸编号时指当前会话。

| 命令 | 行为 |
| --- | --- |
| `/super ddl list [对象\|all]` | 默认当前会话有效任务；私聊 all 查询当前机器人所有个人及群任务 |
| `/super ddl show 对象#编号` | 查看具体任务和历史通知状态 |
| `/super ddl view [对象]` | 将该对象的最近10个有效任务卡片发回 Super 当前会话 |

`list` 支持 `--creator QQ`、`--target QQ`、`--status active|expired|cancelled|all`、`--from "YYYY-MM-DD HH:mm"`、`--to "YYYY-MM-DD HH:mm"`、`--page 页码`。时间过滤针对截止时间，每页20项。名称展示含昵称、群名及对应 ID；跨会话编号始终附带对象前缀。

```text
/super ddl list user:111
/super ddl list all --target 111 --status all
/super ddl list group:3333 --from "2026-11-01 00:00" --to "2026-12-01 00:00"
/super ddl show group:3333#3
/super ddl view user:111
```

## 修改与取消 DDL

```text
/super ddl edit user:111#3 --title "提交物理作业"
/super ddl edit group:3333#3 --due "2026-11-01 18:00"
/super ddl edit user:111#3,group:3333#6 --remind=-1d,-3h,-30min,0
/super ddl edit group:3333#3 --targets 111,222
/super ddl edit group:3333#3 --targets-add 444 --targets-remove 222
/super ddl remove user:111#3,group:3333#6
/super ddl clear group:3333 --dry-run
/super ddl clear user:111
```

- `edit` 至少指定一个字段，只修改有效任务，不调用 AI。Super 不受原设置者限制。
- `--remind` 替换提醒方案，`0` 明确包含到期提醒；管理命令不自动追加到期。
- 仅修改截止时间时，原待发节点按截止时间差平移；仅改标题或通知对象不改变提醒时间。
- 已发送、失败或结果不确定的节点保留，不重复激活；过去节点忽略。
- `--targets` 替换全部对象，不能与增减参数同用；增减可组合，但同一人不能同时增减。目标必须在群里，不能通知机器人；移除最后一人会取消任务。私聊任务只能通知所属用户，不允许改对象。
- `remove` 取消整条任务；`clear` 清除明确会话的全部有效任务，不接受含义含混的 all。保留历史记录和编号。
- 修改、取消后，在每个受影响会话合并发送一次变更说明和刷新卡片；群内 @受影响的现有成员。保存成功但通知失败会单独说明。
- 上述修改命令均支持 `--dry-run`。实际修改也会使基于旧会话数据的在途 AI 创建/修改失效，防止回填旧内容。

## 好友申请、加群申请与入群邀请

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

## 费用、广播与只读群

| 命令 | 行为 |
| --- | --- |
| `/super cost [user QQ号\|group 群号]` | 查询近1、3、7、30天及累计输入/输出 tokens 和人民币费用；不带参数查看当前机器人全部 |
| `/super schedule [user QQ号\|group 群号]` | 查看当前机器人未来待发提醒；不带参数列出全部用户和群，按下一次提醒时间排序 |
| `/super announce` | 每次读取 `src/UPDATE.md` 并广播更新文案 |
| `/super announce text 内容` | 广播指定文字 |
| `/super readonly list` | 私聊查看只读群 |
| `/super readonly add 群号` | 私聊将群设为只读 |
| `/super readonly remove 群号` | 私聊解除只读，不补发旧提醒 |

`schedule` 按 DDL 展示所属会话、设置者、通知对象、截止时间及所有未来 `pending` 提醒节点，不显示已发送、已取消、失败或过期节点，也不显示已取消、全部退订或无剩余提醒的 DDL。`user QQ号` 仅筛选该用户的个人会话，`group 群号` 仅筛选该群。群内 Super 也可查询全部或指定会话，结果发回当前会话；跨平台、其他机器人账号的数据不包含在内。查询不改变调度状态，实际发送仍受 Readonly 等规则约束。

```text
/super schedule
/super schedule user 111
/super schedule group 3333
```

费用按请求发生时配置的输入/输出单价保存，不因改价重算历史。广播仅发给曾与当前机器人私聊、有有效 autoanalysis 权限、未拒收的用户。

默认广播文案保存在 UTF-8 文件 `src/UPDATE.md` 中，修改后下次 `/super announce`（或兼容入口 `/announce`）立即生效，无须修改 Python 代码或重启。文件读取失败或内容为空时停止广播并提示；`/super announce text 内容` 仍可发送自定义文字。

`/send`、`/readonly list` 原本也开放给全局 admin，继续保留。旧 Super 专用 `/role list/add/remove/clear/reset/group-admin`、`/cost`、`/announce`、`/readonly add/remove` 兼容转发一个过渡版本，帮助只展示新入口。不存在独立 `/request` 命令。
