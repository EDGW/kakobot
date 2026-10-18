# 群发送 命令组

[命令目录](README.md) · [Super 管理](super/README.md)

本组涉及以下身份组（不新增身份组）：

- `admin`：全局身份组。

## `/send` 命令

### `/send` - CHAT

**完整格式**：`/send GROUP 内容`

**所需权限组**：`admin`

向目标群发送纯文本，Readonly仍拦截。

### `/send` - GROUP

**完整格式**：`/send GROUP 内容`

**所需权限组**：`admin`

须先真实 @机器人。向目标群发送纯文本，Readonly仍拦截。

## 使用规则与示例

向指定群发送纯文本。Readonly 仍会拦截，Super 也不能绕过。
