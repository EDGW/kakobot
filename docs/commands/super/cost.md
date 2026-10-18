# Super 费用 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组（不新增身份组）：

- `super`：读取用量与账单。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super cost` 命令

### `/super cost` - CHAT

**完整格式**：`/super cost [user QQ号|group 群号]`

**所需权限组**：`super`

近1/3/7/30天及累计 tokens 和人民币费用。

### `/super cost` - GROUP

**完整格式**：`/super cost [user QQ号|group 群号]`

**所需权限组**：`super`

须先真实 @机器人。近1/3/7/30天及累计 tokens 和人民币费用。

## 使用规则与示例

统计近1、3、7、30天及累计输入/输出 tokens 和人民币费用。不带参数查询当前平台与机器人全部数据；user 按请求操作者筛选，group 按请求来源群筛选。CHAT 和 GROUP 均可指定对象，结果发回当前会话。

费用按请求发生时配置的输入/输出单价保存，不因后续改价重算历史；输出 usage 已包含思考 tokens，不会重复累计。
