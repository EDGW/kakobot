# Super DDL 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：跨会话查询和管理。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super ddl list` 命令

### `/super ddl list` - CHAT

**完整格式**：`/super ddl list [this|user:QQ|group:群号|all] [--creator QQ] [--target QQ] [--status active|expired|cancelled|all] [--from 时间] [--to 时间] [--page 页码]`

**所需权限组**：`super`

默认查询当前会话有效任务，每页20项；可按设置者、通知对象、状态及截止时间区间筛选，编号附带会话前缀。私聊可指定个人或群会话。

### `/super ddl list` - GROUP

**完整格式**：`/super ddl list [this|group:本群群号] [--creator QQ] [--target QQ] [--status active|expired|cancelled|all] [--from 时间] [--to 时间] [--page 页码]`

**所需权限组**：`super`

须先真实 @机器人。默认查询当前会话有效任务，每页20项；可按设置者、通知对象、状态及截止时间区间筛选，编号附带会话前缀。只能管理当前群，不能指定其他群、个人会话或 all。

## `/super ddl show` 命令

### `/super ddl show` - CHAT

**完整格式**：`/super ddl show 对象#编号`

**所需权限组**：`super`

查看指定会话任务和所有历史通知状态。私聊可指定个人或群会话。

### `/super ddl show` - GROUP

**完整格式**：`/super ddl show group:本群群号#编号`

**所需权限组**：`super`

须先真实 @机器人。查看指定会话任务和所有历史通知状态。只能管理当前群，不能指定其他群、个人会话或 all。

## `/super ddl view` 命令

### `/super ddl view` - CHAT

**完整格式**：`/super ddl view [this|user:QQ|group:群号]`

**所需权限组**：`super`

将目标会话最近10个有效任务的卡片发回 Super 当前会话，不发送给目标会话。私聊可指定个人或群会话。

### `/super ddl view` - GROUP

**完整格式**：`/super ddl view [this|group:本群群号]`

**所需权限组**：`super`

须先真实 @机器人。将目标会话最近10个有效任务的卡片发回 Super 当前会话，不发送给目标会话。只能管理当前群，不能指定其他群、个人会话或 all。

## `/super ddl edit` 命令

### `/super ddl edit` - CHAT

**完整格式**：`/super ddl edit 对象#编号[,对象#编号] [--title "名称"] [--due "YYYY-MM-DD HH:mm"] [--remind=-3h,-30min,0] [--targets QQ,QQ|--targets-add QQ,QQ|--targets-remove QQ,QQ] [--dry-run]`

**所需权限组**：`super`

至少指定一个字段，仅修改有效任务，不调用 AI。支持标题、截止、提醒方案及群通知对象；不受原设置者限制。私聊可指定个人或群会话。

### `/super ddl edit` - GROUP

**完整格式**：`/super ddl edit group:本群群号#编号[,group:本群群号#编号] [--title "名称"] [--due "YYYY-MM-DD HH:mm"] [--remind=-3h,-30min,0] [--targets QQ,QQ|--targets-add QQ,QQ|--targets-remove QQ,QQ] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。至少指定一个字段，仅修改有效任务，不调用 AI。支持标题、截止、提醒方案及群通知对象；不受原设置者限制。只能管理当前群，不能指定其他群、个人会话或 all。

## `/super ddl remove` 命令

### `/super ddl remove` - CHAT

**完整格式**：`/super ddl remove 对象#编号[,对象#编号] [--dry-run]`

**所需权限组**：`super`

批量取消整条任务的未发通知，保留历史和编号。私聊可指定个人或群会话。

### `/super ddl remove` - GROUP

**完整格式**：`/super ddl remove group:本群群号#编号[,group:本群群号#编号] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。批量取消整条任务的未发通知，保留历史和编号。只能管理当前群，不能指定其他群、个人会话或 all。

## `/super ddl clear` 命令

### `/super ddl clear` - CHAT

**完整格式**：`/super ddl clear this|user:QQ|group:群号 [--dry-run]`

**所需权限组**：`super`

清除明确会话的全部有效任务；必须给出范围，不支持 all。私聊可指定个人或群会话。

### `/super ddl clear` - GROUP

**完整格式**：`/super ddl clear this|group:本群群号 [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。清除明确会话的全部有效任务；必须给出范围，不支持 all。只能管理当前群，不能指定其他群、个人会话或 all。

## 使用规则与示例

对象写作 `user:QQ`（个人任务）、`group:群号`（群任务）或 `this`（当前会话）。完整编号如 `user:111#3`、`group:3333#3`；只有裸编号时指当前会话。


`list` 支持 `--creator QQ`、`--target QQ`、`--status active|expired|cancelled|all`、`--from "YYYY-MM-DD HH:mm"`、`--to "YYYY-MM-DD HH:mm"`、`--page 页码`。时间过滤针对截止时间，每页20项。名称展示含昵称、群名及对应 ID；跨会话编号始终附带对象前缀。

```text
/super ddl list user:111
/super ddl list all --target 111 --status all
/super ddl list group:3333 --from "2026-11-01 00:00" --to "2026-12-01 00:00"
/super ddl show group:3333#3
/super ddl view user:111
```

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
