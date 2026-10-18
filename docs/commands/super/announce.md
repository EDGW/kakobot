# Super 广播 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：发起广播。
- `autoanalysis`：接收人须有的有效权限。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super announce` 命令

### `/super announce` - CHAT

**完整格式**：`/super announce [text 广播内容]`

**所需权限组**：`super`

默认每次读取 UTF-8 文件 `src/UPDATE.md` 并广播；修改该文件后下次发送立即生效，无须修改 Python 或重启。文件读取失败或内容为空时停止发送并提示。

`/super announce text 内容` 广播指定文字，不读取更新文件。广播附带“【广播】”标题和 `/announce-reject on` 拒收提示。

仅发送给与当前机器人有私聊记录、有有效 autoanalysis 权限且未拒收的用户；不向群广播。发起命令可以在私聊或群聊，进度与完成统计发回发起会话。

同一平台与机器人同一时间只运行一场广播，逐人发送并重新检查权限与接收偏好；Super 权限失效时停止。失败逐项统计，不影响其他符合条件的接收人。

兼容入口 `/announce`、`/announce text 内容` 转发至此命令。

```text
/super announce
/super announce text 提醒：今晚18点前提交报告
```

### `/super announce` - GROUP

**完整格式**：`/super announce [text 广播内容]`

**所需权限组**：`super`

默认每次读取 UTF-8 文件 `src/UPDATE.md` 并广播；修改该文件后下次发送立即生效，无须修改 Python 或重启。文件读取失败或内容为空时停止发送并提示。

`/super announce text 内容` 广播指定文字，不读取更新文件。广播附带“【广播】”标题和 `/announce-reject on` 拒收提示。

仅发送给与当前机器人有私聊记录、有有效 autoanalysis 权限且未拒收的用户；不向群广播。发起命令可以在私聊或群聊，进度与完成统计发回发起会话。

同一平台与机器人同一时间只运行一场广播，逐人发送并重新检查权限与接收偏好；Super 权限失效时停止。失败逐项统计，不影响其他符合条件的接收人。

兼容入口 `/announce`、`/announce text 内容` 转发至此命令。

```text
/super announce
/super announce text 提醒：今晚18点前提交报告
```
