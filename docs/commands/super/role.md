# Super 身份组 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：管理权限。
- `admin`、`autoanalysis`、`ddl`、`summary`：可管理的全局组。
- `group.admin`、`group.ddl`、`group.summary`：按群管理的身份组。
- `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`：按平台、机器人和群管理的 AI 对话身份组。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super role show` 命令

### `/super role show` - CHAT

**完整格式**：`/super role show QQ[,QQ] [--page 页码]`

**所需权限组**：`super`

查询一个或多个指定用户的权限，不修改授权。显示直接授权、有效权限及每项权限的来源（直接授予、继承、全员模式）。

`QQ[,QQ]` 为必填用户列表，英文逗号分隔，最多100人；`--page` 为正整数，默认1，每页20人，越界会提示。

显示全局权限及各群权限。

```text
/super role show 111,222
/super role show 111,222 --page 1
```

### `/super role show` - GROUP

**完整格式**：`/super role show QQ[,QQ] [--page 页码]`

**所需权限组**：`super`

查询一个或多个指定用户的权限，不修改授权。显示直接授权、有效权限及每项权限的来源（直接授予、继承、全员模式）。

`QQ[,QQ]` 为必填用户列表，英文逗号分隔，最多100人；`--page` 为正整数，默认1，每页20人，越界会提示。

显示全局权限及本群权限，不展示其他群授权。

```text
/super role show 111,222
/super role show 111,222 --page 1
```

## `/super role list` 命令

### `/super role list` - CHAT

**完整格式**：`/super role list [ROLE] [--group 群号] [--source direct|inherited|everyone] [--page 页码]`

**所需权限组**：`super`

按身份组、群和权限来源筛选用户，省略 ROLE 时列出查询范围内有有效授权的用户。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`；群角色使用 `群号.admin`、`群号.ddl`、`群号.summary`，例如 `3333.ddl`。

- `--group 群号`：仅保留该群实际成员，并查询该群角色；与 ROLE 中的群号同时出现时须一致。 私聊不指定群时按角色或已知授权范围查询。
- `--source direct`：匹配直接授权来源。
- `--source inherited`：匹配通过上级身份组继承的权限。
- `--source everyone`：匹配全员 group.admin 模式产生的权限。
- 不指定 source 时不按来源筛选；来源筛选用于筛选人员，展示仍包含其权限说明。
- `--page`：正整数，默认1，每页20人。

此命令只查询，不改变权限。

```text
/super role list autoanalysis --source inherited
/super role list --group 3333 --page 2
```

### `/super role list` - GROUP

**完整格式**：`/super role list [ROLE] [--group 本群群号] [--source direct|inherited|everyone] [--page 页码]`

**所需权限组**：`super`

按身份组、群和权限来源筛选用户，省略 ROLE 时列出查询范围内有有效授权的用户。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`，群角色使用 `group.admin`、`group.ddl`、`group.summary` 或 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`，仅代表当前群。

- `--group 群号`：仅保留该群实际成员，并查询该群角色；与 ROLE 中的群号同时出现时须一致。 群内只能指定本群，省略时默认本群。
- `--source direct`：匹配直接授权来源。
- `--source inherited`：匹配通过上级身份组继承的权限。
- `--source everyone`：匹配全员 group.admin 模式产生的权限。
- 不指定 source 时不按来源筛选；来源筛选用于筛选人员，展示仍包含其权限说明。
- `--page`：正整数，默认1，每页20人。

此命令只查询，不改变权限。

```text
/super role list autoanalysis --source inherited
/super role list --group 3333 --page 2
```

## `/super role add` 命令

### `/super role add` - CHAT

**完整格式**：`/super role add QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

为列表中的每个用户添加列表中的每项直接授权，保留其所有其他授权。已持有的直接授权不会重复添加。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`；群角色使用 `群号.admin`、`群号.ddl`、`群号.summary`，例如 `3333.ddl`。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role add 111,222 ddl,3333.ddl --dry-run
```

### `/super role add` - GROUP

**完整格式**：`/super role add QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

为列表中的每个用户添加列表中的每项直接授权，保留其所有其他授权。已持有的直接授权不会重复添加。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`，群角色使用 `group.admin`、`group.ddl`、`group.summary` 或 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`，仅代表当前群。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role add 111,222 ddl,group.ddl --dry-run
```

## `/super role remove` 命令

### `/super role remove` - CHAT

**完整格式**：`/super role remove QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

从每个指定用户移除明确列出的直接授权，不改变其余授权，也不会屏蔽从上级身份组继承的权限。

例如用户经 admin 继承 ddl，仅移除 ddl 的直接授权后，仍然拥有有效 ddl；若要撤销该权限，须处理产生继承的授权来源。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`；群角色使用 `群号.admin`、`群号.ddl`、`群号.summary`，例如 `3333.ddl`。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role remove 111,222 3333.ddl --dry-run
```

### `/super role remove` - GROUP

**完整格式**：`/super role remove QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

从每个指定用户移除明确列出的直接授权，不改变其余授权，也不会屏蔽从上级身份组继承的权限。

例如用户经 admin 继承 ddl，仅移除 ddl 的直接授权后，仍然拥有有效 ddl；若要撤销该权限，须处理产生继承的授权来源。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`，群角色使用 `group.admin`、`group.ddl`、`group.summary` 或 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`，仅代表当前群。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role remove 111,222 group.ddl --dry-run
```

## `/super role set` 命令

### `/super role set` - CHAT

**完整格式**：`/super role set QQ[,QQ] ROLE[,ROLE] --scope global|group:群号 [--dry-run]`

**所需权限组**：`super`

将每个指定用户在单一范围内的全部直接授权替换为 ROLE 列表，范围之外保持原样。与 add 不同，未出现在列表中的原直接授权会被移除。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`；群角色使用 `群号.admin`、`群号.ddl`、`群号.summary`，例如 `3333.ddl`。

`--scope` 必填：`global` 表示全局，`group:群号` 表示单个群；ROLE 必须全部属于该范围，不允许混入全局和群角色。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role set 111,222 ddl,summary --scope global --dry-run
```

### `/super role set` - GROUP

**完整格式**：`/super role set QQ[,QQ] ROLE[,ROLE] --scope global|group:本群群号|group [--dry-run]`

**所需权限组**：`super`

将每个指定用户在单一范围内的全部直接授权替换为 ROLE 列表，范围之外保持原样。与 add 不同，未出现在列表中的原直接授权会被移除。

`ROLE` 可写全局 `admin`、`autoanalysis`、`ddl`、`summary`，群角色使用 `group.admin`、`group.ddl`、`group.summary` 或 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`，仅代表当前群。

`--scope` 必填：`global` 表示全局，`group:群号` 表示单个群；ROLE 必须全部属于该范围，不允许混入全局和群角色。 群内还可用 `--scope group` 表示本群，不得指定其他群。

QQ 和 ROLE 列表以英文逗号分隔，各最多100项；QQ 必须为正整数。配置的 `super` 可查询，不能通过命令授予、移除或覆盖。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role set 111,222 group.ddl --scope group --dry-run
```

## `/super role clear` 命令

### `/super role clear` - CHAT

**完整格式**：`/super role clear QQ[,QQ] --scope global|group:群号|all [--dry-run]`

**所需权限组**：`super`

清空指定用户在明确范围内的全部直接授权。它不接受 ROLE 列表；仅移除某项角色请用 remove。不会撤销其他来源的继承或全员模式权限，也不取消已有 DDL。

`--scope` 必填：`global` 清空全局直接授权，`group:群号` 清空单群直接授权。 `all` 同时清空全局及所有已知群的直接授权，仅私聊可用。

QQ 列表用英文逗号分隔，最多100人；配置的 super 不受影响。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role clear 111,222 --scope group:3333 --dry-run
```

### `/super role clear` - GROUP

**完整格式**：`/super role clear QQ[,QQ] --scope global|group:本群群号|group [--dry-run]`

**所需权限组**：`super`

清空指定用户在明确范围内的全部直接授权。它不接受 ROLE 列表；仅移除某项角色请用 remove。不会撤销其他来源的继承或全员模式权限，也不取消已有 DDL。

`--scope` 必填：`global` 清空全局直接授权，`group:群号` 清空单群直接授权。 群内可用 `group` 表示本群，不能指定其他群或 all。

QQ 列表用英文逗号分隔，最多100人；配置的 super 不受影响。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role clear 111,222 --scope group --dry-run
```

## `/super role reset` 命令

### `/super role reset` - CHAT

**完整格式**：`/super role reset 群号[,群号] [--roles group.ddl,group.summary] [--dry-run]`

**所需权限组**：`super`

针对群的授权名单操作：移除目标群里所有人所持有的指定直接群身份组，而不是只清理某几个用户。

群号必填，多个群用英文逗号分隔，最多100群。

`--roles` 省略时清空全部六种群直接授权（含 group.discuss.super/admin/user）；提供时只清空列出的角色，使用英文逗号分隔。roles 使用 `group.ddl` 这样的名称。

不改变全局授权、不关闭全员 group.admin 模式，也不取消现有 DDL；其他继承或全员模式仍可能让用户保持有效权限。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role reset 3333,4444 --roles group.ddl,group.summary --dry-run
```

### `/super role reset` - GROUP

**完整格式**：`/super role reset [本群群号] [--roles group.ddl,group.summary] [--dry-run]`

**所需权限组**：`super`

针对群的授权名单操作：移除目标群里所有人所持有的指定直接群身份组，而不是只清理某几个用户。

群号可省略，默认本群；显式群号也只能是本群。

`--roles` 省略时清空全部六种群直接授权（含 group.discuss.super/admin/user）；提供时只清空列出的角色，使用英文逗号分隔。roles 使用 `group.ddl` 这样的名称。

不改变全局授权、不关闭全员 group.admin 模式，也不取消现有 DDL；其他继承或全员模式仍可能让用户保持有效权限。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role reset --roles group.ddl,group.summary --dry-run
```

## `/super role group-admin` 命令

### `/super role group-admin` - CHAT

**完整格式**：`/super role group-admin on|off 群号[,群号] [--dry-run]`

**所需权限组**：`super`

切换群的“全员 group.admin”模式，不改动已保存的直接授权名单。

- `on`：所有实际群成员获得 group.admin，并继承 group.ddl 与 group.summary。
- `off`：恢复按授权名单及继承关系判断；不会清空原直接授权。

必须提供群号；多个群用英文逗号分隔，最多100群。

这是机器人内部权限开关，不改变 QQ 原生群管理员身份。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role group-admin on 3333,4444 --dry-run
/super role group-admin off 3333,4444
```

### `/super role group-admin` - GROUP

**完整格式**：`/super role group-admin on|off [本群群号] [--dry-run]`

**所需权限组**：`super`

切换群的“全员 group.admin”模式，不改动已保存的直接授权名单。

- `on`：所有实际群成员获得 group.admin，并继承 group.ddl 与 group.summary。
- `off`：恢复按授权名单及继承关系判断；不会清空原直接授权。

省略群号时作用于本群，不能指定其他群。

这是机器人内部权限开关，不改变 QQ 原生群管理员身份。

支持 `--dry-run` 只预览，不保存、不通知。批量操作先完整校验，再一次性保存，并记录操作者、时间和前后权限。

```text
/super role group-admin on --dry-run
/super role group-admin off
```

## discuss 统一身份管理

支持 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`；私聊编码为 `群号.discuss.super`、`群号.discuss.admin`、`群号.discuss.user`。继承 super → admin → user，独立于 group.admin。按当前平台、机器人账号和群隔离，专用 discuss 命令共用同一份授权。

```text
/super role add 10002 123456.discuss.admin
/super role remove 10002 123456.discuss.admin
/super role list 123456.discuss.super
```

上述管理命令须全局 super，普通用户通过 `/role` 查看自身。all/blacklist 模式影响有效 user，直接白名单授权与有效权限分别展示。黑名单不能撤销管理身份继承；全员 group.admin 不授予 discuss。clear/set/reset 同样覆盖目标范围的 discuss 直接授权，不清空 discuss 黑名单和准入模式。
