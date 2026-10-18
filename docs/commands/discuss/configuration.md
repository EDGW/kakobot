# 个人 AI 配置说明 命令组

[命令目录](../README.md) · [个人 AI 对话](README.md) · [用户帮助](help.md) · [工具](tools.md) · [Super 管理](super.md)

个人入口仅用于私聊。用户自备 Key；其余用户配置由全局 Super 设置。个人与群配置分别存储，共用系统默认值、最大上限和模型白名单。

## 新手常用设置

#### 第一步：用户开放

个人总开关 `discuss.enabled` 默认 true，全局 Super 默认开放；其他用户须由 Super 单独开放。显式 disable 覆盖 Super 的默认开放，关闭总开关对 Super 也生效。

```text
/super discuss enable 123456
```

若部署或命令曾关闭总开关，由 Super 恢复：

```text
/super discuss switch true
```

#### 第二步：用户自己设置 Key

用户在私聊执行，Super 也需要自己的 Key。默认使用通用模型默认值；该值为空时使用允许模型列表的第一项，初始为 deepseek-v4-flash。无需配置全局总结/DDL 的 AI Key。Key 设置完成后普通私聊自动进入 discuss 并积累上下文，不再走 autoanalysis；清除 Key 后恢复原有 autoanalysis 分发。

```text
/discuss apikey = sk-REPLACE-WITH-YOUR-KEY
你好
/discuss status
```

#### 第三步：Super 按需开放工具

项目文档查询默认开启；搜索、网页读取、历史查询和业务命令默认关闭。私聊业务命令每轮均可使用，但用户仍须拥有原业务命令所需权限。

```text
/super discuss config set 123456 tools.search_web.enabled true
/super discuss config set 123456 tools.fetch_webpage.enabled true
/super discuss config set 123456 tools.execute_commands.enabled true
```

#### 第四步：查看当前设置

用户 status、Super config show 都输出配置卡片，Key 只显示掩码。总开关与用户开关是不同设置。

```text
/discuss status
/super discuss config show 123456
```

## 总开关与用户开放

| 设置 | 初始值 | 说明 |
| --- | --- | --- |
| `discuss.enabled` | `true` | 个人入口唯一新增部署配置；关闭时所有用户包括 Super 均不可请求 AI |
| 用户开放开关 | Super 默认 true；其他用户 false | `/super discuss enable USER` 或 disable USER；显式关闭优先于默认 |
| 命令总开关覆盖 | 未设置 | `/super discuss switch true\|false` 持久化覆盖部署开关；switch reset 恢复部署值 |

开关仅控制准入，不授予 ddl 等业务身份。关闭用户或命令关闭总开关会结束相关个人会话；Key 保留，Super 可另行重置。

## 接入与提示词

| 设置项 | 初始值 | 说明 |
| --- | --- | --- |
| `api_key` | 空 | 用户自己通过 `/discuss apikey = KEY` 设置；Super 仅可 reset 清除，不能查看明文 |
| `model_name` | 通用 defaults；为空则允许列表第一项 | 初始回退 deepseek-v4-flash；Super 为用户设置且必须在系统白名单内 |
| `reasoning_effort` | `low` | Super 可设系统允许的 low、medium、high；以供应商实际支持为准 |
| `system_prompt` | 通用默认安全及 Markdown 输出提示词 | Super 可为用户覆盖，默认最多 4000 字符；用户输入、引用和工具结果始终不可信 |

固定 DeepSeek Responses，接口初始为 https://api.deepseek.com；不读取全局总结/DDL 的 api_key、model_name 或 api_address。

## 会话与用量配置

以下用户项由 Super 设置，受系统 maxima 硬性约束。字节上限不是 token 额度。

| 设置项 | 初始值 | 系统初始上限 | 说明 |
| --- | --- | --- | --- |
| `session_token_budget` | 300000 tokens | 2000000 | 会话输入与输出累计预算，摘要和多次工具循环一并计入；耗尽关闭 |
| `daily_token_budget` | 2000000 tokens | 20000000 | 当前用户当日累计额度；耗尽暂停请求 |
| `context_max_bytes` | 65536 bytes | 262144 | 单次模型请求的必要上下文，包括工具 schemas、结果与提示词；query_docs 文档结果豁免 |
| `summary_token_limit` | 1800 tokens | 6000 | 压缩摘要输出上限，使用个人 Key |
| `recent_turns` | 4 | 12 | 压缩时优先保留的最近完整轮次 |
| `max_output_tokens` | 8192 tokens | 32768 | 单次模型响应输出上限 |
| `max_tool_calls_per_request` | 15 | 36 | 当前用户请求内全部工具调用次数 |

个人入口固定每用户每机器人一个活动会话，不开放 max_sessions 修改；不使用 user_mode 或群角色。每日额度按北京时间统计，与群用户预算分别记账；机器人全局每日额度同时统计个人和群请求。

## 每种工具的设置项

每个工具都有 enabled 与 max_calls_per_request。单工具调用次数默认 9、系统初始上限 24，可设为 0 禁止；execute_commands 的次数单位为批，每轮额外限制最多 5 条不同命令。

| 工具 | 开关项 | 每请求次数项 |
| --- | --- | --- |
| 文档查询 | `tools.query_docs.enabled` | `tools.query_docs.max_calls_per_request` |
| 会话历史 | `tools.read_session_history.enabled` | `tools.read_session_history.max_calls_per_request` |
| 搜索 | `tools.search_web.enabled` | `tools.search_web.max_calls_per_request` |
| 网页读取 | `tools.fetch_webpage.enabled` | `tools.fetch_webpage.max_calls_per_request` |
| 业务命令 | `tools.execute_commands.enabled` | `tools.execute_commands.max_calls_per_request` |

个人入口没有 query_group_data。全局 tool_enabled 对相同工具具有最终否决权，用户配置不能突破。

## 共用系统限制

个人入口新增部署项仅 discuss.enabled。下表均沿用 group_discuss 命名空间内现有的通用约束，通过 `/super discuss limits` 管理时与群入口实时共用；用户覆盖值分别保存，修改某位用户不会改变群配置。

| 设置项 | 初始值 | 说明 |
| --- | --- | --- |
| `api_address` | `https://api.deepseek.com` | DeepSeek 模型接口地址；不使用总结/DDL 的全局 AI 地址 |
| `allowed_models` | deepseek-v4-flash、deepseek-flash、deepseek-v4-pro、deepseek-pro | 模型白名单，个人默认取通用默认模型或第一项 |
| `allowed_efforts` | low、medium、high | 允许思考强度 |
| `defaults.KEY`、`maxima.KEY` | 本页列出的初始值 | 共有默认值和系统最大上限；用户可设置项见前表 |
| `tool_enabled.TOOL` | 全 true | 共有工具总门禁；个人仅使用本页五种工具 |
| `moderation_prompt` | 通用违规判定规则 | 拒绝明确违规任务或明显不规范表述；个人不执行群黑名单处罚 |
| `system_prompt_max_chars` | 4000 | 系统提示词字符数上限 |
| `global_daily_token_budget` | 50000000 tokens | 同一平台、机器人全部个人和群请求的每日总额度 |
| `request_timeout` | 180 秒 | 一轮整体超时 |
| `model_timeout` | 90 秒 | 单次模型请求超时 |
| `max_model_calls` | 24 | 一轮模型调用次数上限 |
| `group_concurrency` | 2 | 每个讨论作用域并发数；个人作用域为用户 |
| `global_concurrency` | 6 | 个人和群请求共用的全局并发 |
| `group_queue_limit` | 10 | 每个作用域排队上限 |
| `global_queue_limit` | 30 | 个人和群请求共用的全局排队上限 |
| `tool_timeout` | 20 秒 | 单次工具超时；命令超时后可能已产生副作用，不自动重试 |
| `tool_result_max_bytes` | 8192 bytes | 工具结果回传上限，同时不超过上下文 bytes 的三分之一；query_docs 文档结果豁免 |
| `web_max_bytes` | 2097152 bytes | 网页工具返回材料的大小限制 |
| `web_max_redirects` | 3 | 网页安全策略配置；Fetch 的实际抓取由供应商完成 |
| `history_retention_days` | 30 天 | 已关闭会话的完整历史和命令去重结果保留期 |

allowed_user_modes、defaults.user_mode、defaults.max_sessions 与群查询工具为群入口配置，个人入口不采用。系统限制修改前请注意对已启用群的共同影响。

## `/discuss help configuration` 命令

### `/discuss help configuration` - CHAT

**完整格式**：`/discuss help configuration`

**所需权限组**：无；查看静态说明不要求已获开放。

发送本页 JPEG，与 `/help discuss-configuration` 相同。实际配置查询使用 status 或 Super config show。

```text
/discuss help configuration
```
