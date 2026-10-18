# 配置与升级

[返回 README](../README.md)

## 配置项

| 配置 | 默认 | 说明 |
| --- | --- | --- |
| `super_user` | `000000000` | 唯一 Super 的 QQ；占位值不授予权限 |
| `api_address` | `https://api.openai.com/v1` | 支持 Responses 的 API 基础地址，或完整 `/responses` 地址 |
| `api_key` | 空 | 模型认证密钥 |
| `model_name` | 空 | 服务支持的模型名称 |
| `reasoning_effort` | 空 | 留空不传；按服务支持填写 low、medium、high 等 |
| `input_price_per_million_cny` | 0 | 每百万输入 tokens 的人民币单价，非负 |
| `output_price_per_million_cny` | 0 | 每百万输出 tokens 的人民币单价，非负 |
| `enabled_analysis_tasks` | `["ddl"]` | 目前仅支持 ddl，空列表关闭自动分析 |
| `autoanalysis_disabled_users` | `[]` | 暂停这些 QQ 的自动分析，保留身份组及手动命令权限 |

模型请求使用 Responses、`store=false`，没有历史会话记忆或工具。不支持 Responses 的中转服务需要更换兼容接口。输入按整体 tokens 单价估算，不单独折扣缓存；输出 usage 包含的思考 tokens 不重复累计。缺失 usage 不伪造为零。

## 存储与升级

运行数据只写 AstrBot 的 `StarTools.get_data_dir("astrbot_plugin_kakobot")` 目录：

| 文件 | 内容 |
| --- | --- |
| `version.json` | 成功迁移后的版本标记 |
| `roles.json` | 直接授权和按群的全员模式开关 |
| `readonly.json` | 独立只读群名单 |
| `ddl_preferences.json` | 各用户自动识别默认提醒提示词 |
| `deadlines.sqlite3` | DDL、提醒状态、自动分析去重 |
| `usage.sqlite3` | 用量与请求当时的价格、费用 |
| `conversations.sqlite3` | 私聊记录和广播拒收偏好 |
| `requests.sqlite3` | 好友/群申请、去重凭据和处理状态 |
| `management.sqlite3` | 管理操作前后数据与执行状态 |

升级前停止旧插件，备份整个数据目录。版本标记缺失时视为0.5.4，先备份、迁移并校验成功后再启动；支持从已兼容的 1.x、alpha 和 beta 版本保留数据升级到 v2.0.0.beta.2。迁移失败或发现未知、损坏的数据会停止启动，不清空重建。旧版备份位于 `migration-backup-0.5.4/`。不要手工预写成功标记，或让新旧版本同时访问数据。

群权限开关沿用已有存储语义：`group_admin_enabled=true` 为按名单校验，false 为全员 group.admin；用户命令中的 `on` 指开启全员模式。

## 日志与发送

AstrBot INFO 日志记录每次模型请求的完整正文和完整回复，并对配置的 API Key 脱敏；日志可能含聊天正文，请按自己的数据管理要求保存。API Key 通过认证交给配置的模型服务，不进入提示词和 QQ 消息，已观察过的旧 Key 在本次运行期仍受保护。

出站 QQ 内容统一检查受保护 Key，超过15行的文本自动使用合并聊天记录，图片直接发出。请求、模型、存储和发送等完整错误只通知 Super，普通用户收到简短错误；正常成功不额外发送错误日志。

Readonly 在命令入口、DDL 写入和发送处独立检查。调度每15秒扫描，离线、过旧或被 Readonly 跳过的节点不补发；发送失败或结果不确定不自动重试。提醒按原平台和机器人账号路由，不选择其他连接替代。

旧版本迁移成功后，机器人账号连接就绪时会自动私聊发送 `src/UPDATE.md` 更新公告。接收条件与 `/super announce` 相同：有私聊记录、有效 autoanalysis 权限且未拒收；全新安装和普通重启不发送。按版本和接收人持久化发送状态，连接未就绪时等待；发送失败或结果不确定不自动重试。

## 群 AI 对话

`group_discuss` 为独立配置命名空间，不使用上述总结/DDL 凭据；所有群初始关闭。全局 Super 配置 DeepSeek Responses 地址、模型白名单并启用目标群。具体配置见 [discuss 配置](commands/group-discuss/configuration.md)。

新增 `group_discuss.sqlite3`（群身份、配置、加密历史、预算账本）、`group_discuss.key`（独立加密主密钥）及 `group_discuss_policy.json`（全局命令配置覆盖）。备份时保留密钥文件；丢失后不能解密已有凭据，启动会拒绝覆盖。群 Key 不进入审计或用量明文。


## 个人 AI 对话

`discuss.enabled` 是个人入口唯一新增部署配置，初始 true。全局 Super 默认开放；其他用户由 `/super discuss enable USER` 单独开启。显式用户关闭与总开关关闭同样约束 Super。每位用户通过私聊 `/discuss apikey = KEY` 设置自己的 DeepSeek Key；设置后普通私聊自动进入 discuss 并累积上下文，/new 重置话题，移除 Key 后恢复原有 autoanalysis 分发。全部个人模型请求、摘要和联网都使用此 Key，不回退到上方总结/DDL 的全局 AI 设置。

个人文档独立位于 [个人配置](commands/discuss/configuration.md) 与 [个人命令目录](commands/discuss/README.md)，群配置仍见 [群配置](commands/group-discuss/configuration.md)。个人沿用 `group_discuss` 内现有的通用默认值、上限、模型白名单与全局工具门禁，用户覆盖单独保存；共用系统策略可由 `/super discuss limits` 管理，对个人和群同时生效。

个人与群共用 `group_discuss.sqlite3` 账本和加密主密钥，个人按平台、机器人、CHAT、用户隔离，与群及其他用户的 Key、历史、配置和用户预算互不混用。机器人每日总额度和并发统一控制。新增 `discuss_switch.json` 只保存个人总开关的命令覆盖；`/super discuss switch reset` 恢复部署值。备份应包含整个数据目录。

工具业务命令使用原有 KakoBot 权限检查：私聊每轮可用，群聊仅新会话首轮可用，不提供系统命令。审计只记录操作者、会话、命令名及执行状态；命令结果加密保存，Key 不进入明文记录。
