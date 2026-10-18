# 广播偏好 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组（不新增身份组）：

- 无；所有用户可用。

## `/announce-reject` 命令

### `/announce-reject` - CHAT

**完整格式**：`/announce-reject on|off`

**所需权限组**：无；所有用户可用。

on 拒收全部广播，off 恢复接收；不影响 DDL 提醒。

### `/announce-reject` - GROUP

**完整格式**：`/announce-reject on|off`

**所需权限组**：无；所有用户可用。

须先真实 @机器人。on 拒收全部广播，off 恢复接收；不影响 DDL 提醒。

## 使用规则与示例

`on` 拒收本机器人的全部广播，`off` 恢复；群内设置也只改变操作者本人的偏好。DDL 提醒不受影响。恢复后仍需有私聊记录和有效 `autoanalysis` 权限才会收到广播。
