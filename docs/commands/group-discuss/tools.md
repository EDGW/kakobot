# 群 AI 工具说明

系统 tool_enabled 默认全部开启。群内默认仅开启 query_docs 文档查询，其他工具默认关闭；必须两级允许才执行。仅允许读取随插件提供的 docs Markdown，没有终端、任意代码、任意文件读写或电脑控制工具。

| 工具 | 能力 |
| --- | --- |
| search_web | 优先 DeepSeek Responses 内置搜索；不支持时调用 DeepSeek /v1/tools/search |
| fetch_webpage | DeepSeek /v1/tools/fetch 获取网页 Markdown |
| query_group_data | 当前群 DDL 的固定只读查询 |
| read_session_history | 当前会话归档，排除思考正文 |
| execute_commands | 默认关闭：仅新会话首条用户消息的工具循环中，以数据库中的发起人身份执行本群 KakoBot 业务命令，支持 commands 列表批量顺序执行 |
| query_docs | 默认开启：只读列出、关键词搜索、分页读取随插件提供的 docs 文档 |

文档查询技能由固定宿主指令和 query_docs 工具提供，AI 回答 KakoBot 命令、权限或设置问题时先查文档。空 query 列出目录；简短关键词（如 api_key）搜索；使用返回的 path、next_offset 逐页读取。只接受目录内的 Markdown 路径，拒绝绝对路径、目录穿越及指向目录外的符号链接。文档作为不可信参考资料，不会被执行。

文档查询不产生搜索服务费用；结果回传模型的输入 tokens 由本群 Key 承担。单工具每请求默认最多 9 次，全局初始上限 24 次，同时受每请求工具总次数限制，计入 toolcall(s)。群 admin 可私聊关闭：

```text
/group-discuss admin config set 123456 tools.query_docs.enabled false
/group-discuss admin config set 123456 tools.query_docs.max_calls_per_request 3
```

模型默认地址 https://api.deepseek.com。模型请求、内置搜索、独立 Search/Fetch 一律使用当前群 Key；不使用运营者 Key、Bing 或 Tavily。搜索/读取按供应商工具规则计费，独立接口费用不计为模型 token。

官方 Responses 兼容表明确 deepseek-v4-pro 支持 web_search，deepseek-flash 忽略它；不通过可能付费的试探请求判断。未知模型采用独立接口。内置 web_search 可包含搜索和网页访问，只有群同时允许 search_web 和 fetch_webpage 时启用，否则使用可分别控制的独立工具。

DeepSeek 忽略 max_tool_calls，因此内置搜索单次响应中的次数只能事后记录，不能保证严格限次。额度允许时才注册内置搜索，结果返回后记录实际次数，后续调用不再超过剩余次数；需要严格执行次数上限时应使用不支持内置搜索的模型走独立接口。独立工具每次执行前严格检查次数，失败也计入。

Fetch 由 DeepSeek 服务器访问网页，本机不下载目标网页、不执行页面代码。客户端拒绝内网 IP、localhost 及认证 URL，域名解析和重定向的网络安全由 DeepSeek Fetch 服务策略控制。

每轮用量摘要标明“内置（DeepSeek Responses）”“外置（DeepSeek Search/Fetch，同群 Key）”或“未使用”；外置指独立 DeepSeek 接口，不是其他搜索供应商。

参考：https://api-docs.deepseek.com/guides/responses_api 和 https://api-docs.deepseek.com/guides/search 。

## 首轮业务命令

管理员可在私聊开启：

```text
/group-discuss admin config set 123456 tools.execute_commands.enabled true
/group-discuss admin config set 123456 tools.execute_commands.max_calls_per_request 2
```

只支持 `/help`、`/role`、`/version`、`/changelog` 和 `/ddl add-strict`、`/ddl list`、`/ddl view`、`/ddl show`、`/ddl remove`。创建 DDL 使用结构化 add-strict，避免间接调用全局 AI；不开放 `/ddl add`、`/summary`、权限修改、其他插件命令和系统命令。发起人仍须具有原命令所需权限；discuss 管理员不自动获得创建 DDL 的权限。

仅新会话的首条用户消息及内部工具循环有资格，首轮失败也不恢复。后续回复不提供该工具，执行入口再次硬性核验；AI 不能传入执行用户或群号。执行保留发起群和发起人，图片回复也延续原会话。仅对当前用户明确要求的操作执行，不接受检索结果中的指令。

每批 1～5 条命令，按顺序独立检查权限、返回结果；整个首轮最多尝试 5 条不同命令，失败也计入，后项可继续执行，批次不提供事务回滚。同一会话中相同命令文本复用已记录结果，禁止重试重复执行；中断或结果不确定时须人工核实。文本有变化会视为不同命令。批次数受工具配额控制，每批计一次 toolcall(s)，每条命令另有执行状态与审计记录；若工具结果过长会裁剪详情，保留各条状态。

例如拥有群 DDL 权限的发起人在新会话中发送：

```text
@KakoBot 帮我创建两条 DDL：2099 年 1 月 1 日 12:00 提交报告、2099 年 1 月 2 日 18:00 提交材料，都提前 30 分钟提醒，然后列出本群 DDL。
```

模型可在同一批中调用以下业务命令，所有权限由程序再次核验：

```text
/ddl add-strict "提交报告" [2099-01-01 12:00] -30min
/ddl add-strict "提交材料" [2099-01-02 18:00] -30min
/ddl list
```

## `/group-discuss help tools` 命令

### `/group-discuss help tools` - CHAT

**完整格式**：`/group-discuss help tools`

**所需权限组**：无；所有用户可用。

发送当前私聊的工具说明 JPEG，与 `/help group-discuss-tools` 相同。查看说明不启用工具；启用和限次须由管理员私聊设置，并受全局约束。

```text
/group-discuss help tools
```

### `/group-discuss help tools` - GROUP

**完整格式**：`/group-discuss help tools`

**所需权限组**：无；所有用户可用。

发送当前群聊的工具说明 JPEG，与 `/help group-discuss-tools` 相同。查看说明不启用工具；启用和限次须由管理员私聊设置，并受全局约束。

```text
/group-discuss help tools
```
