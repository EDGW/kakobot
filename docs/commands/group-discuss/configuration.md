# 群 AI 对话配置

[命令目录](../README.md) · [群管理命令](admin.md) · [全局 Super 命令](super.md) · [工具说明](tools.md) · [预算与统计](statistics.md)

## 新手常用设置

下面以群 `123456`、群负责人 `10001`、普通用户 `10002` 为例。请替换为实际群号、QQ 号和 Key。**本节所有配置命令都在私聊机器人时执行。**

#### 第一步：全局 Super 开通

由系统 `super_user` 指定的账号操作。默认已允许 `deepseek-v4-flash`、`deepseek-flash`、`deepseek-v4-pro`、`deepseek-pro`，无需手动添加模型白名单。

```text
/super group-discuss limits show
/super group-discuss enable 123456 10001
```

模型地址默认是 `https://api.deepseek.com`，通常不需要修改。功能默认未开通；enable 开通目标群，并将 `10001` 加入本群 `group.discuss.super`。群 super 继承 admin，可继续完成后续配置。

#### 第二步：群负责人配置 Key、模型和用户

```text
/group-discuss admin config set 123456 api_key sk-YOUR-DEEPSEEK-KEY
/group-discuss admin config set 123456 model_name deepseek-flash
/group-discuss admin user add 10002 123456
/group-discuss admin config show 123456
```

模型必须在全局白名单内，且本群 Key 可调用该模型。默认 `user_mode` 为 whitelist，上面只放行指定用户；群 admin/super 自带 user 权限。普通用户进群后 @ 机器人开始对话，回复机器人的回答继续原会话。

如果希望所有群成员都能使用，可将准入方式改为 all：

```text
/group-discuss admin config set 123456 user_mode all
```

#### 第三步：按需调整预算、联网和提示词

默认每个会话预算 300000 tokens，每群每日预算 2000000 tokens，最多同时保留 5 个活跃会话。先保持默认即可；需要调整时：

```text
/group-discuss admin config set 123456 max_sessions 5
/group-discuss admin config set 123456 session_token_budget 300000
/group-discuss admin config set 123456 daily_token_budget 2000000
```

**群内默认只开启项目文档查询，联网和其他工具默认关闭。** 需要搜索和读取网页时再启用：

```text
/group-discuss admin config set 123456 tools.search_web.enabled true
/group-discuss admin config set 123456 tools.fetch_webpage.enabled true
```

模型、内置搜索和独立 Search/Fetch 均由本群 DeepSeek Key 付费，不使用运营者的搜索凭据。工具服务费用独立于模型 token，token 预算不能代替工具费用上限。支持内置搜索的模型在两个联网开关都开启时优先使用内置能力；内置搜索的响应内次数无法硬性限制，详见 [工具说明](tools.md)。

自定义本群回答要求，并查看当日用量：

```text
/group-discuss admin config set 123456 system_prompt "请使用简洁中文，回答附必要来源，拒绝危险任务"
/group-discuss admin stats 123456 today
```

## 配置范围与生效规则

| 范围 | 管理者 | 修改入口 | 作用 |
| --- | --- | --- | --- |
| 本群配置 | 本群 discuss admin、群 super、全局 super | `/group-discuss admin config` | 只影响指定群 |
| 系统配置 | 全局 super | `/super group-discuss limits`；部署配置中的 `group_discuss` | 控制所有群的默认值、上限、允许集合及运行限制 |
| 功能启停 | 全局 super | `/super group-discuss enable`、`disable` | 开通或停用目标群；停用时结束该群全部会话 |

全局 super 始终可以接管任意群。群 super 的任免、群 admin 的任免和用户名单属于身份管理，见 [群管理命令](admin.md) 与 [全局管理命令](super.md)，不是 config 设置项。

本页表格均为程序初始值，实际值以 show 输出为准。未单独设置的群配置继承系统 defaults；群内显式设置会覆盖对应默认值。修改系统 defaults 会影响仍在继承该项的群。

- 群数值超出全局 maxima 时拒绝保存；全局上限收紧后，现有数值按新上限生效。
- 工具必须同时满足系统总开关和群开关；系统禁止后，群内已保存的 true 也不会生效。
- 模型、思考强度或准入模式不再被系统允许时，暂停相关调用并要求修正，不自动替换。
- 配置在后续调用前重新检查；已经提交供应商的请求仍可能产生费用。

## 群配置：Key、模型与用户准入

| 设置项 | 初始值 | 作用与可选值 |
| --- | --- | --- |
| `api_key` | 未设置 | 本群 DeepSeek Key，非空时长度 8～512 字符；空字符串或 reset 清除。查看仅展示 `sk-XX*****XX`，不返回原文 |
| `model_name` | 未设置 | 本群使用的 DeepSeek 模型，必须属于系统 `allowed_models`；未配置时不能对话 |
| `reasoning_effort` | `low` | 思考强度，初始允许 `low`、`medium`、`high`；须同时被系统和目标模型支持 |
| `user_mode` | `whitelist` | 普通用户准入方式：whitelist、all 或 blacklist，且须在系统 `allowed_user_modes` 内 |
| `system_prompt` | 下方默认提示词 | 本群系统提示词，非空文本；初始最多 4000 字符，受系统 `system_prompt_max_chars` 约束 |

准入方式具体含义：

| 模式 | 普通用户可使用的条件 |
| --- | --- |
| `whitelist` | 本群成员，且有本群 user 直接授权 |
| `all` | 本群所有成员 |
| `blacklist` | 本群成员，且不在本群 discuss 黑名单中 |

名单通过 `/group-discuss admin user add|remove` 和 `/group-discuss admin blacklist add|remove` 管理。切换模式不清空名单。群 admin/super 继承 user，黑名单或撤销 user 直接授权不能覆盖这种继承；全局 super 始终有管理权和有效 user 权限。

系统默认提示词原文：

> 符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容

`system_prompt` 同时用于回答和历史摘要。reset 后重新继承系统默认提示词。所有普通用户输入、网页、引用及历史摘要均视为不可信资料，不能覆盖系统规则；修改提示词不会增加电脑控制、跨群访问或绕过预算的能力。若系统字符上限收紧使现有提示词超限，调用暂停，调整提示词后恢复。

## 群配置：会话、预算与上下文

除单工具次数允许设为 0 外，下表数值均为正整数。表中的“系统初始上限”可由全局 super 调整。

| 设置项 | 群初始默认 | 系统初始上限 | 作用与达到限制后的行为 |
| --- | --- | --- | --- |
| `max_sessions` | 5 | 20 | 群内活跃会话上限；超过时按创建时间结束最早会话，降低配置立即淘汰超额会话 |
| `session_token_budget` | 300000 | 2000000 | 单会话累计输入加输出预算；不足以预留下一次调用时自动结束会话 |
| `daily_token_budget` | 2000000 | 20000000 | 本群每日输入加输出预算；耗尽后暂停调用，次日可继续未结束会话 |
| `context_max_bytes` | 65536 | 262144 | 单次模型请求的 UTF-8 字节上限（含 JSON 序列化及 256 bytes 协议预留），不是 tokens；历史接近上限时尝试摘要，必要输入仍超限时拒绝调用 |
| `summary_token_limit` | 1800 | 6000 | 历史摘要的最大输出 tokens；实际输出同时受 max_output_tokens 限制，摘要消耗也记入预算 |
| `recent_turns` | 4 | 12 | 压缩时优先保留的最近完整轮次数；少数长轮次占满上下文时可进一步缩减保留范围 |
| `max_output_tokens` | 8192 | 32768 | 每次正常回答模型请求的输出上限；同时约束摘要请求的输出，不代表整轮工具循环的输出总和 |
| `max_tool_calls_per_request` | 15 | 36 | 一条用户请求内全部工具的累计次数，跨多次模型调用累计；内置搜索有供应商限次限制 |

“会话”是可由回复链多次延续的一段交流；“一条用户请求”是用户的一次发言及其全部内部模型、工具和摘要调用。压缩只缩短下一次发送的上下文，不结束会话，也不清零累计预算。

每日按北京时间 00:00 切换。预算包含重复历史、缓存输入和摘要的输入/输出消耗；缓存命中是输入的子集，不重复累加。调用前先预留，收到 usage 后结算；缺失 usage 时保留预留，不能按零处理。输入限制与裁剪使用 bytes；输出、摘要及累计预算使用 tokens。预留 token 预算仍以输入字节数作为保守上界，再加最大输出 tokens，可能提前拒绝；结算及实际账单以供应商 usage 为准。完整记账规则见 [预算与统计](statistics.md)。

## 群配置：每种工具的开关与限次

五种工具分别具有两个独立设置项，下面列出全部十项。文档查询 query_docs 的群开关初始为 true，其他群开关为 false；单工具每请求次数初始为 9，系统初始上限为 24，允许设置为 0 以禁止该工具执行。

| 工具 | 群开关设置项 | 单工具次数设置项 | 能力 |
| --- | --- | --- | --- |
| 搜索 | `tools.search_web.enabled` | `tools.search_web.max_calls_per_request` | 搜索公开互联网；支持的模型优先使用 Responses 内置搜索，否则调用 DeepSeek Search |
| 网页读取 | `tools.fetch_webpage.enabled` | `tools.fetch_webpage.max_calls_per_request` | 调用 DeepSeek Fetch 读取公开 HTTP(S) 网页正文 |
| 群数据查询 | `tools.query_group_data.enabled` | `tools.query_group_data.max_calls_per_request` | 只读查询当前群 DDL，不修改业务数据 |
| 会话历史 | `tools.read_session_history.enabled` | `tools.read_session_history.max_calls_per_request` | 读取本会话归档，每次最多 8 条消息项，排除思考正文 |
| 项目文档查询 | `tools.query_docs.enabled` | `tools.query_docs.max_calls_per_request` | 默认开启，只读搜索、列出和分页读取随插件提供的 docs 文档 |

独立工具执行前检查单工具和总次数，实际执行失败也计次数。内置搜索可包含网页访问，须同时允许搜索和网页读取；DeepSeek 忽略内置搜索的 max_tool_calls，客户端只能记录响应返回的动作并阻止后续超额调用，无法保证单次响应内不超限。

示例：搜索每请求最多 2 次，全部工具累计最多 4 次；这两个设置对独立接口执行硬限制。

```text
/group-discuss admin config set 123456 tools.search_web.max_calls_per_request 2
/group-discuss admin config set 123456 max_tool_calls_per_request 4
```

## 系统配置：默认值、上限与允许集合

以下设置仅全局 super 可改。命令中的 KEY 不需要加 `group_discuss.` 前缀；部署配置中则位于该命名空间内。

| 设置项 | 初始值 | 作用 |
| --- | --- | --- |
| `api_address` | `https://api.deepseek.com` | DeepSeek OpenAI Responses 兼容接口的基地址；须为无认证信息、查询参数和片段的 HTTPS 地址。独立 Search/Fetch 始终请求 DeepSeek 官方工具接口 |
| `allowed_models` | `["deepseek-v4-flash","deepseek-flash","deepseek-v4-pro","deepseek-pro"]` | 可用模型白名单，默认包含这四个模型，无需手动添加；全局 super 仍可按需替换，仅接受 DeepSeek 模型名 |
| `allowed_efforts` | `["low","medium","high"]` | 群可选择的思考强度；仍需目标模型支持 |
| `allowed_user_modes` | `["whitelist","all","blacklist"]` | 群可选择的用户准入方式 |
| `defaults.KEY` | 本页各群初始值 | 设置群继承的默认配置；KEY 可为任一群设置项，但不包括 api_key |
| `maxima.KEY` | 本页各数值初始上限 | 设置群数值项的最大值，包括五种工具各自的次数；不用于字符串、枚举和开关 |
| `tool_enabled.search_web` | `true` | 是否允许各群开启搜索 |
| `tool_enabled.fetch_webpage` | `true` | 是否允许各群开启网页读取 |
| `tool_enabled.query_group_data` | `true` | 是否允许各群开启当前群 DDL 查询 |
| `tool_enabled.read_session_history` | `true` | 是否允许各群开启本会话历史读取 |
| `tool_enabled.query_docs` | `true` | 是否允许各群查询项目文档；默认各群开启 |
| `system_prompt_max_chars` | 4000 字符 | 群系统提示词长度上限 |

因此，“系统允许工具”和“群默认启用工具”是两项不同设置：初始 tool_enabled 全 true，defaults 中仅 tools.query_docs.enabled 为 true，其余四种工具为 false。群开关即使已设为 true，也不能突破系统禁用。

```text
/super group-discuss limits set defaults.max_sessions 5
/super group-discuss limits set maxima.max_sessions 20
/super group-discuss limits set defaults.tools.search_web.enabled false
/super group-discuss limits set maxima.tools.search_web.max_calls_per_request 8
/super group-discuss limits set tool_enabled.search_web true
```

## 系统配置：预算、超时、并发与保留

这些数值配置均为正整数，校验上界为 10 亿；应按实际资源和费用设置，校验上界不是建议值。

| 设置项 | 初始值 | 作用 |
| --- | --- | --- |
| `global_daily_token_budget` | 50000000 tokens | 所有群合计的机器人每日模型预算；耗尽后暂停新调用，群 Key 各自结算费用 |
| `request_timeout` | 180 秒 | 一条用户请求的整体执行超时，覆盖内部模型、工具和摘要处理 |
| `model_timeout` | 90 秒 | 单次模型 HTTP 请求超时 |
| `max_model_calls` | 24 次 | 一条用户请求最多提交的模型调用次数，包含摘要和工具循环 |
| `group_concurrency` | 2 | 单群最多同时处理的请求数 |
| `global_concurrency` | 6 | 所有群合计最多同时处理的请求数 |
| `group_queue_limit` | 10 | 单群等待队列容量；排队还需同时满足全局限制 |
| `global_queue_limit` | 30 | 所有群合计等待队列容量 |
| `tool_timeout` | 20 秒 | 单次工具执行超时 |
| `tool_result_max_bytes` | 8192 bytes | 单次工具结果正文上限；按 UTF-8 字节裁剪，并取 context_max_bytes 的三分之一与本值中较小者，不是实际计费 tokens |
| `web_max_bytes` | 2097152 字节（2 MiB） | 独立 Search/Fetch 接口响应体大小上限；本机不直接下载目标网页 |
| `web_max_redirects` | 3 | 旧版网页抓取保留项；当前 DeepSeek Search/Fetch 不使用该值，客户端不跟随工具接口重定向，目标网页跳转由 DeepSeek 服务处理 |
| `history_retention_days` | 30 天 | 已结束会话正文的保留时间；启动时清理过期正文，用量账本继续保留 |

## 查看、修改与恢复配置

### `/group-discuss admin config` - CHAT

**完整格式**：`/group-discuss admin config show GROUP [KEY]`、`/group-discuss admin config set GROUP KEY VALUE`、`/group-discuss admin config reset GROUP KEY`

**所需权限组**：目标群 `group.discuss.admin`（含群 super 继承）或全局 `super`。

- GROUP：目标群号，必须填写。
- KEY：本页列出的群设置项；show 省略 KEY 时查看全部。
- VALUE：新值。布尔值用 true/false，数值直接填写，含空格的文本用引号包裹。
- show：发送配置卡片图片，按接入、预算、工具和提示词分区展示生效值、来源及相关系统约束。群覆盖被全局限制时同时列出存储值；Key 只显示脱敏值。指定 KEY 时只展示该项和相关约束。
- reset：删除本群覆盖值，重新继承当前系统默认；api_key 则清除，不重置历史消耗。

```text
/group-discuss admin config show 123456
/group-discuss admin config show 123456 daily_token_budget
/group-discuss admin config set 123456 reasoning_effort low
/group-discuss admin config reset 123456 system_prompt
```

### `/group-discuss admin config` - GROUP

群聊不可用。请私聊机器人并指定群号。

### `/super group-discuss limits` - CHAT

**完整格式**：`/super group-discuss limits show`、`/super group-discuss limits set KEY VALUE`

**所需权限组**：全局 `super`。

show 查看全部系统设置；set 修改指定项。默认模型白名单已可使用，下方调整白名单的命令仅为可选示例，会替换整个列表，应保留其他群仍在使用的模型。数组或对象使用 JSON，并用单引号包裹，字符串中的空格使用引号。这些命令没有 reset 子命令；需要恢复时用 set 显式写入目标值。

```text
/super group-discuss limits show
/super group-discuss limits set allowed_models '["deepseek-flash","deepseek-v4-pro"]'
/super group-discuss limits set global_daily_token_budget 5000000
```

### `/super group-discuss limits` - GROUP

群聊不可用。请私聊机器人操作。

## 配置存储与备份

全局 limits 命令写入插件数据目录的 `group_discuss_policy.json`，优先于部署 config 中的同名设置；使用过命令覆盖后，再调整该项请继续使用 limits 命令，避免部署值被旧覆盖遮住。

群凭据与历史使用 cryptography Fernet 加密，主密钥位于数据目录的 `group_discuss.key`；备份时同时保存主密钥和数据库。Key 不进入提示词、工具参数、统计或审计正文；不会回退使用总结或 DDL 功能的模型凭据。独立 search_api_key 已不再使用。

## 旧配置自动升级

启动识别到旧配置版本时，自动迁移群数据库和持久化系统策略。旧 context_token_limit 改为 context_max_bytes，旧 tool_result_tokens 改为 tool_result_max_bytes。新命令仅使用新字段名；summary_token_limit 仍为真实的输出 tokens。

与旧默认值相同的额度升级到本页新默认值，非默认自定义额度保留原数值（旧输入限制原本就按 bytes 执行）。未单独设置的群项继续继承系统策略。升级不清空历史、用量、密钥或权限；迁移完成后记录版本，重启不重复提升管理员后来调整的额度。
