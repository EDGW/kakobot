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

## discuss 统一身份管理

支持 `group.discuss.super`、`group.discuss.admin`、`group.discuss.user`；私聊编码为 `群号.discuss.super`、`群号.discuss.admin`、`群号.discuss.user`。继承 super → admin → user，独立于 group.admin。按当前平台、机器人账号和群隔离，专用 discuss 命令共用同一份授权。

```text
/super role add 10002 123456.discuss.admin
/super role remove 10002 123456.discuss.admin
/super role list 123456.discuss.super
```

上述管理命令须全局 super，普通用户通过 `/role` 查看自身。all/blacklist 模式影响有效 user，直接白名单授权与有效权限分别展示。黑名单不能撤销管理身份继承；全员 group.admin 不授予 discuss。clear/set/reset 同样覆盖目标范围的 discuss 直接授权，不清空 discuss 黑名单和准入模式。
