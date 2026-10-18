# 广播偏好 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组：

- 无；所有用户可用。

## `/announce-reject` 命令

### `/announce-reject` - CHAT

**完整格式**：`/announce-reject on|off`

**所需权限组**：无；所有用户可用。

`on` 拒收本机器人的全部广播，`off` 恢复；群内设置也只改变操作者本人的偏好。DDL 提醒不受影响。恢复后仍需有私聊记录和有效 `autoanalysis` 权限才会收到广播。

必须明确提供 on 或 off，不带参数、额外参数或其他值会报用法错误。偏好按当前平台与机器人账号保存，不影响其他机器人的广播。

```text
/announce-reject on
/announce-reject off
```

### `/announce-reject` - GROUP

**完整格式**：`/announce-reject on|off`

**所需权限组**：无；所有用户可用。

`on` 拒收本机器人的全部广播，`off` 恢复；群内设置也只改变操作者本人的偏好。DDL 提醒不受影响。恢复后仍需有私聊记录和有效 `autoanalysis` 权限才会收到广播。

必须明确提供 on 或 off，不带参数、额外参数或其他值会报用法错误。偏好按当前平台与机器人账号保存，不影响其他机器人的广播。

```text
/announce-reject on
/announce-reject off
```
