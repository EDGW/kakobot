# 身份查询 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组：

- 无；所有用户可用。

## `/role` 命令

### `/role` - CHAT

**完整格式**：`/role`

**所需权限组**：无；所有用户可用。

查看本人的全局身份组，以及全部已知群的身份组。

输出区分直接授权和有效权限，并给出继承等来源。不接受其他用户 QQ、角色名或修改参数；授予和撤销使用 [Super 身份组命令](super/role.md)。

全局继承为 `super → admin → autoanalysis → ddl、summary`；群内继承为 `group.admin → group.ddl、group.summary`。群身份组按群隔离，不代表 QQ 原生管理员。

```text
/role
```

### `/role` - GROUP

**完整格式**：`/role`

**所需权限组**：无；所有用户可用。

查看本人的全局身份组，以及当前群的身份组，不展示其他群的授权。

输出区分直接授权和有效权限，并给出继承等来源。不接受其他用户 QQ、角色名或修改参数；授予和撤销使用 [Super 身份组命令](super/role.md)。

全局继承为 `super → admin → autoanalysis → ddl、summary`；群内继承为 `group.admin → group.ddl、group.summary`。群身份组按群隔离，不代表 QQ 原生管理员。

```text
/role
```
