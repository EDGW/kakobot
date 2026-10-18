# 群 AI 工具说明

系统 tool_enabled 默认全部开启，群开关默认全部关闭；必须两级允许才执行。没有终端、任意代码、文件读写或电脑控制工具。

| 工具 | 能力 |
| --- | --- |
| search_web | 优先 DeepSeek Responses 内置搜索；不支持时调用 DeepSeek /v1/tools/search |
| fetch_webpage | DeepSeek /v1/tools/fetch 获取网页 Markdown |
| query_group_data | 当前群 DDL 的固定只读查询 |
| read_session_history | 当前会话归档，排除思考正文 |

模型默认地址 https://api.deepseek.com。模型请求、内置搜索、独立 Search/Fetch 一律使用当前群 Key；不使用运营者 Key、Bing 或 Tavily。搜索/读取按供应商工具规则计费，独立接口费用不计为模型 token。

官方 Responses 兼容表明确 deepseek-v4-pro 支持 web_search，deepseek-flash 忽略它；不通过可能付费的试探请求判断。未知模型采用独立接口。内置 web_search 可包含搜索和网页访问，只有群同时允许 search_web 和 fetch_webpage 时启用，否则使用可分别控制的独立工具。

DeepSeek 忽略 max_tool_calls，因此内置搜索单次响应中的次数只能事后记录，不能保证严格限次。额度允许时才注册内置搜索，结果返回后记录实际次数，后续调用不再超过剩余次数；需要严格执行次数上限时应使用不支持内置搜索的模型走独立接口。独立工具每次执行前严格检查次数，失败也计入。

Fetch 由 DeepSeek 服务器访问网页，本机不下载目标网页、不执行页面代码。客户端拒绝内网 IP、localhost 及认证 URL，域名解析和重定向的网络安全由 DeepSeek Fetch 服务策略控制。

每轮用量摘要标明“内置（DeepSeek Responses）”“外置（DeepSeek Search/Fetch，同群 Key）”或“未使用”；外置指独立 DeepSeek 接口，不是其他搜索供应商。

参考：https://api-docs.deepseek.com/guides/responses_api 和 https://api-docs.deepseek.com/guides/search 。

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
