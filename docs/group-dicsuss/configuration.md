# discuss 配置

所有实际设置的查看与修改仅限私聊，必须填写群号。群 admin、群 super 和全局 super 可操作，Key 只展示 `sk-XX*****XX`，无法查看原文。

```text
/group-discuss admin config show GROUP [KEY]
/group-discuss admin config set GROUP KEY VALUE
/group-discuss admin config reset GROUP KEY
```

show 展示存储值、生效值及全局约束；reset 恢复系统默认，api_key 则清除。超出全局范围直接拒绝；全局数值上限收紧时立即限制生效值。

| KEY | 群默认 | 初始全局最大值 |
| --- | --- | --- |
| max_sessions | 5 | 20 |
| session_token_budget | 30000 | 200000 |
| daily_token_budget | 200000 | 2000000 |
| context_token_limit | 6000 | 24000 |
| summary_token_limit | 600 | 2000 |
| recent_turns | 4 | 12 |
| max_output_tokens | 2048 | 8192 |
| max_tool_calls_per_request | 5 | 12 |
| tools.NAME.max_calls_per_request | 3 | 8 |

其他设置：`user_mode` 默认 whitelist；`api_key`、`model_name` 初始未设置；`reasoning_effort` 默认 low；`tools.NAME.enabled` 默认 false。工具、模型和思考强度必须在系统允许范围内。摘要上限必须小于上下文上限。

模型地址、允许模型/思考强度/准入模式、全局工具开关、默认值和上限位于系统 `group_discuss` 配置；仅全局 super 管理，不回退使用总结或 DDL 的模型凭据。DeepSeek 地址与模型白名单初始留空，必须根据实际兼容端点配置。

```text
/super group-discuss limits show
/super group-discuss limits set api_address https://YOUR-DEEPSEEK-ENDPOINT/v1
/super group-discuss limits set allowed_models '["deepseek-YOUR-MODEL"]'
/super group-discuss limits set maxima.max_sessions 20
/super group-discuss limits set tool_enabled.search_web true
/super group-discuss limits set search_api_key YOUR-TAVILY-KEY
```

数组和对象使用 JSON，命令行用单引号包裹 JSON。普通字符串无需加引号。low/medium/high 是初始允许集合，目标模型是否支持需实际验证；不自动切换供应商或协议。

运行初始约束：全机器人每日 5000000 tokens；每轮总超时 180 秒、单模型请求 90 秒、模型调用最多 8 次；单群并发 2、全局并发 6；单群排队 10、全局排队 30；工具超时 20 秒、结果 3000 tokens、网页 2 MiB、重定向 3 次；已结束会话正文保留 30 天。

全局命令变更持久化到插件数据目录 `group_discuss_policy.json`，作为部署 config 的覆盖值；再次调整请使用 limits 命令，避免只改被覆盖的部署值。群凭据和历史使用 cryptography Fernet 加密，主密钥独立保存在 `group_discuss.key`，应与数据库一起备份，支持文件系统权限保护。搜索 Key 在系统配置中提供时，部署配置文件本身的访问权限由部署者管理。

## 群系统提示词

群设置 `system_prompt` 继承系统 `group_discuss.defaults.system_prompt`。系统默认原文：

> 符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容

```text
/group-discuss admin config show GROUP system_prompt
/group-discuss admin config set GROUP system_prompt "本群提示词"
/group-discuss admin config reset GROUP system_prompt
```

仅限私聊。本群 discuss admin/super 和全局 super 可修改。非空文本最多 4000 字符，上限由系统 `system_prompt_max_chars` 控制。系统上限收紧导致已有提示词超限时暂停调用，须调整后恢复。

所有用户输入默认不可信，不能覆盖系统规则。群提示词用于每次正常回答及摘要请求，不赋予电脑控制、跨群查询、绕过预算或身份鉴权能力。
