# Summary 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组（不新增身份组）：

- `summary`：私聊总结。
- `admin`：群内总结及跨群读取。
- `group.summary`：当前群总结。

## `/summary` 命令

### `/summary` - CHAT

**完整格式**：`/summary`，附带或引用文字、聊天记录。

**所需权限组**：`summary`

总结本次提供且可读取的正文或聊天记录，不关联历史私聊。不会通过历史 get_msg 补取不可读取的引用。

### `/summary text` - CHAT

**完整格式**：`/summary text 内容`

**所需权限组**：`summary`

直接总结参数中的文字。

### `/summary group` - CHAT

**完整格式**：`/summary group 群号`，也可使用 `/summary 群号`。

**所需权限组**：`summary`；非全局 `admin` 还必须是目标群实际成员。

读取目标群接口可获取的近期消息并总结；全局 admin 可跨群读取。

### `/summary` - GROUP

**完整格式**：`/summary`

**所需权限组**：`admin` 或 `group.summary`

须先真实 @机器人。读取当前群近期可获取的消息并总结。

### `/summary 群号` - GROUP

**完整格式**：`/summary 群号`

**所需权限组**：全局 `admin`

须先真实 @机器人。读取明确指定群的近期消息；只有 group.summary 时不能使用带群号的格式。

## 使用规则

群历史最多读取接口可获取的100条，不能保证获得全部历史或 QQ 未读状态。总结末行显示 `（+xxxx tokens used)`，未返回有效用量则显示未知。

请求真正提交模型后先发送等待提示；Readonly 群不处理命令，也不能作为发送结果的目标。
