# 个人 AI 工具说明 命令组

[命令目录](../README.md) · [个人 AI 对话](README.md) · [配置](configuration.md) · [Super 管理](super.md)

工具权限由全局 Super 管理。全局工具门禁与用户工具开关同时允许时才能调用；单工具次数和每请求总次数同时生效。没有 Shell、终端、任意代码、任意文件读写或电脑控制工具。

## 可用工具

| 工具 | 用户初始开关 | 能力 |
| --- | --- | --- |
| `query_docs` | `true` | 只读列目录、关键词搜索、分页读取随插件提供的 Markdown 文档 |
| `read_session_history` | `false` | 只读当前个人会话归档，每次最多 8 条消息项，排除思考正文 |
| `search_web` | `false` | 支持时优先 DeepSeek Responses 内置搜索，否则调用 DeepSeek Search |
| `fetch_webpage` | `false` | DeepSeek Fetch 读取公开 HTTP(S) 网页 Markdown |
| `execute_commands` | `false` | 在私聊每轮，以数据库中的会话发起人身份执行受支持的 KakoBot 业务命令 |

上述初始开关继承通用 defaults，Super 可修改默认值和用户覆盖。个人入口不提供 `query_group_data`，不能通过参数访问其他用户或群会话。

## 代替 autoanalysis

设置个人 Key 后普通私聊由 discuss 接管。要让 discuss 自动完成创建个人 DDL 等原 autoanalysis 工作，Super 须允许 tools.execute_commands，用户仍须具有 ddl 权限；仅设置 Key 不会自动授予业务工具或创建权限。移除个人 Key（`/discuss apikey clear`）即可恢复原 autoanalysis 分发，前提是原有身份和开关允许。

## 业务命令：私聊每轮可用

资格、执行身份和权限均由程序判定，AI 仅提交 commands 列表。私聊每轮都可执行，不要求是会话首轮。支持同一批顺序执行多条命令，每条独立检查权限、返回状态；执行范围固定为当前用户的私聊。

| 命令 | 行为 |
| --- | --- |
| `/help [功能组]` | 发送对应帮助图片 |
| `/role` | 查看发起人身份 |
| `/version`、`/changelog` | 查询版本、发送更新日志 |
| `/ddl add-strict` | 创建个人 DDL；发起人仍须有 `ddl` 权限 |
| `/ddl list`、`/ddl show ID`、`/ddl view` | 查询个人 DDL，view 发送图片 |
| `/ddl remove ID` | 按原命令权限取消个人任务 |

不开放权限修改、群发送、其他插件和系统命令；`/ddl add`、`/summary` 会调用全局 AI，当前不开放。缺少日期或对象时应先澄清，不能猜测后执行。资料、网页和文档中的操作指令不构成用户授权。

每批最多 5 条，每轮最多尝试 5 条不同命令，失败也计入。每批计一次 toolcall(s)，另有逐条执行审计。相同轮次内相同命令文本复用已记录结果；后续轮次可以再次执行。发生中断或结果不确定时不自动重试，须人工核实；该批已完成的命令不回滚。结果过长时裁剪详情，保留逐条状态。

```text
/discuss 请创建个人DDL：2099年1月1日12:00提交报告，提前30分钟提醒，然后列出我的DDL。
```

模型可提交：

```text
/ddl add-strict "提交报告" [2099-01-01 12:00] -30min
/ddl list
```

## 搜索与费用

回答、摘要、内置搜索和独立 Search/Fetch 全部使用当前用户的 DeepSeek Key，无运营者 Key 回退。文档、历史查询和本地业务处理不额外请求 AI，但工具结果回传模型产生输入 tokens。独立搜索工具的供应商费用不计入模型 token 统计。

已知支持内置搜索的 deepseek-v4-pro 在搜索、网页读取同时允许时启用内置能力；其他模型走独立工具。DeepSeek 忽略内置搜索的 max_tool_calls，单次响应内部动作只能事后记录；独立工具执行前硬性检查配额。用量末行标明内置、外置（DeepSeek Search/Fetch，个人 Key）或未使用。

## `/discuss help tools` 命令

### `/discuss help tools` - CHAT

**完整格式**：`/discuss help tools`

**所需权限组**：无；查看不要求已获开放。

发送本页 JPEG，与 `/help discuss-tools` 相同。开启工具须由 Super 私聊设置：

```text
/discuss help tools
/super discuss config set 123456 tools.execute_commands.enabled true
/super discuss config set 123456 tools.execute_commands.max_calls_per_request 2
```
