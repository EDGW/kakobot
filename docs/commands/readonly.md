# 只读群查询 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组：

- `admin`：全局身份组。

## `/readonly list` 命令

### `/readonly list` - CHAT

**完整格式**：`/readonly list`

**所需权限组**：`admin`

仅私聊可用，群内没有此入口。修改只读群名单见 [Super 只读群管理](super/readonly.md)。Readonly 群不处理 DDL 命令，也不发送群提醒；解除后不补发已跳过的旧提醒。
