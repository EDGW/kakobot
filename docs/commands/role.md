# 身份查询 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组（不新增身份组）：

- 无；所有用户可用。

## `/role` 命令

### `/role` - CHAT

**完整格式**：`/role`

**所需权限组**：无；所有用户可用。

查看本人全局身份组和全部群身份组，包含有效权限与继承来源。

### `/role` - GROUP

**完整格式**：`/role`

**所需权限组**：无；所有用户可用。

须先真实 @机器人。查看本人全局身份组与当前群身份组，不展示其他群的授权。

## 使用规则与示例

全局权限继承：`super → admin → autoanalysis → ddl、summary`；群内继承：`group.admin → group.ddl、group.summary`。群身份组按群隔离，与 QQ 原生管理员无关。

这里只查询本人权限，授权与撤销见 [Super 身份组管理](super/role.md)。
