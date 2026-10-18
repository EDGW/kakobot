# Super 身份组 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：管理权限。
- `admin`、`autoanalysis`、`ddl`、`summary`：可管理的全局组。
- `group.admin`、`group.ddl`、`group.summary`：按群管理的身份组。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super role show` 命令

### `/super role show` - CHAT

**完整格式**：`/super role show QQ[,QQ] [--page 页码]`

**所需权限组**：`super`

查询指定用户的直接及有效权限。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role show` - GROUP

**完整格式**：`/super role show QQ[,QQ] [--page 页码]`

**所需权限组**：`super`

须先真实 @机器人。查询指定用户的直接及有效权限。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role list` 命令

### `/super role list` - CHAT

**完整格式**：`/super role list [ROLE] [--group 群号] [--source direct|inherited|everyone] [--page 页码]`

**所需权限组**：`super`

按身份组、群和来源筛选成员。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role list` - GROUP

**完整格式**：`/super role list [ROLE] [--group 本群群号] [--source direct|inherited|everyone] [--page 页码]`

**所需权限组**：`super`

须先真实 @机器人。按身份组、群和来源筛选成员。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role add` 命令

### `/super role add` - CHAT

**完整格式**：`/super role add QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

批量添加直接授权。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role add` - GROUP

**完整格式**：`/super role add QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。批量添加直接授权。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role remove` 命令

### `/super role remove` - CHAT

**完整格式**：`/super role remove QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

批量移除直接授权，保留继承权限。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role remove` - GROUP

**完整格式**：`/super role remove QQ[,QQ] ROLE[,ROLE] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。批量移除直接授权，保留继承权限。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role set` 命令

### `/super role set` - CHAT

**完整格式**：`/super role set QQ[,QQ] ROLE[,ROLE] --scope global|group:群号 [--dry-run]`

**所需权限组**：`super`

替换指定范围的直接授权。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role set` - GROUP

**完整格式**：`/super role set QQ[,QQ] ROLE[,ROLE] --scope global|group:本群群号|group [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。替换指定范围的直接授权。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role clear` 命令

### `/super role clear` - CHAT

**完整格式**：`/super role clear QQ[,QQ] --scope global|group:群号|all [--dry-run]`

**所需权限组**：`super`

批量清除指定范围直接授权。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role clear` - GROUP

**完整格式**：`/super role clear QQ[,QQ] --scope global|group:本群群号|group [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。批量清除指定范围直接授权。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role reset` 命令

### `/super role reset` - CHAT

**完整格式**：`/super role reset 群号[,群号] [--roles group.ddl,group.summary] [--dry-run]`

**所需权限组**：`super`

清空群的全部或指定直接身份组名单。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role reset` - GROUP

**完整格式**：`/super role reset [本群群号] [--roles group.ddl,group.summary] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。清空群的全部或指定直接身份组名单。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## `/super role group-admin` 命令

### `/super role group-admin` - CHAT

**完整格式**：`/super role group-admin on|off 群号[,群号] [--dry-run]`

**所需权限组**：`super`

开关全员 group.admin 模式，保留直接名单。私聊群身份组写作 群号.admin/ddl/summary。

### `/super role group-admin` - GROUP

**完整格式**：`/super role group-admin on|off [本群群号] [--dry-run]`

**所需权限组**：`super`

须先真实 @机器人。开关全员 group.admin 模式，保留直接名单。群身份组写作 group.admin/group.ddl/group.summary，群范围只能是本群；全局授权仍可管理。

## 使用规则与示例

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
