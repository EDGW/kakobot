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

升级前停止旧插件，备份整个数据目录。版本标记缺失时视为0.5.4，先备份、迁移并校验成功后再启动；支持从 v1.2.2 及已支持的旧版本保留数据升级到 v1.3.1。迁移失败或发现未知、损坏的数据会停止启动，不清空重建。旧版备份位于 `migration-backup-0.5.4/`。不要手工预写成功标记，或让新旧版本同时访问数据。

群权限开关沿用已有存储语义：`group_admin_enabled=true` 为按名单校验，false 为全员 group.admin；用户命令中的 `on` 指开启全员模式。

## 日志与发送

AstrBot INFO 日志记录每次模型请求的完整正文和完整回复，并对配置的 API Key 脱敏；日志可能含聊天正文，请按自己的数据管理要求保存。API Key 通过认证交给配置的模型服务，不进入提示词和 QQ 消息，已观察过的旧 Key 在本次运行期仍受保护。

出站 QQ 内容统一检查受保护 Key，超过15行的文本自动使用合并聊天记录，图片直接发出。请求、模型、存储和发送等完整错误只通知 Super，普通用户收到简短错误；正常成功不额外发送错误日志。

Readonly 在命令入口、DDL 写入和发送处独立检查。调度每15秒扫描，离线、过旧或被 Readonly 跳过的节点不补发；发送失败或结果不确定不自动重试。提醒按原平台和机器人账号路由，不选择其他连接替代。

旧版本迁移成功后，机器人账号连接就绪时会自动私聊发送 `src/UPDATE.md` 更新公告。接收条件与 `/super announce` 相同：有私聊记录、有效 autoanalysis 权限且未拒收；全新安装和普通重启不发送。按版本和接收人持久化发送状态，连接未就绪时等待；发送失败或结果不确定不自动重试。
