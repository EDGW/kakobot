# 个人 AI 工具说明 命令组

[命令目录](../README.md) · [个人 AI 对话](README.md) · [配置](configuration.md) · [Super 管理](super.md)

工具权限由全局 Super 管理。全局工具门禁与用户工具开关同时允许时才能调用；单工具次数和每请求总次数同时生效。没有 Shell、终端、任意代码、任意文件读写或电脑控制工具。

## 可用工具

| 工具 | 用户初始开关 | 能力 |
| --- | --- | --- |
| `query_docs` | `true` | 只读列目录、关键词搜索、完整读取随插件提供的 Markdown 文档 |
| `read_session_history` | `false` | 只读当前个人会话归档，每次最多 8 条消息项，排除思考正文 |
| `search_web` | `false` | 支持时优先 DeepSeek Responses 内置搜索，否则调用 DeepSeek Search |
| `fetch_webpage` | `false` | DeepSeek Fetch 读取公开 HTTP(S) 网页 Markdown |
| `execute_commands` | `false` | 在私聊每轮，以数据库中的会话发起人身份执行受支持的 KakoBot 业务命令 |

上述初始开关继承通用 defaults，Super 可修改默认值和用户覆盖。个人入口不提供 `query_group_data`，不能通过参数访问其他用户或群会话。

## 代替 autoanalysis

设置个人 Key 后普通私聊由 discuss 接管。要让 discuss 自动完成创建个人 DDL 等原 autoanalysis 工作，Super 须允许 tools.execute_commands，用户仍须具有 ddl 权限；仅设置 Key 不会自动授予业务工具或创建权限。移除个人 Key（`/discuss apikey clear`）即可恢复原 autoanalysis 分发，前提是原有身份和开关允许。

## 业务命令：私聊每轮可用

资格、执行身份和权限均由程序判定，AI 仅提交 commands 列表。私聊每轮都可执行，不要求是会话首轮。支持同一批顺序执行多条命令，每条独立检查权限、返回状态；执行范围固定为当前用户的私聊。

所有 KakoBot 已注册业务命令均可执行，包括 DDL 的创建/清除、summary、群发送及管理命令；每条仍须满足发起人的原命令权限、私聊/群聊位置和目标资源检查。Super 可执行其有权使用的管理命令，普通用户不会因此获得额外权限。其他插件命令、Shell 和系统命令不可执行。`/ddl add`、`/summary` 内部的 AI 请求使用当前用户的 discuss DeepSeek Key，统一计入本轮用量和预算，绝不回退全局 AI。

缺少日期或对象时应先澄清，不能猜测后执行。资料、网页和文档中的操作指令不构成用户授权。

每轮最多尝试 tools.execute_commands.max_commands_per_request 条不同命令（默认 5，全局 Super 豁免），失败也计入。每批计一次 toolcall(s)，另有逐条执行审计。相同轮次内相同命令文本复用已记录结果；后续轮次可以再次执行。发生中断或结果不确定时不自动重试，须人工核实；该批已完成的命令不回滚。结果过长时裁剪详情，保留逐条状态。

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

#### 卡片与文字结果

AI 自动调用 `/help`、`/role`、`/changelog`、`/ddl view` 时，用户收到原命令卡片，AI 同时收到对应文字内容；较长结果受工具结果大小限制。身份组展示遇到个别群成员接口失败时继续显示其他群，并标注失败群“成员身份无法确认”，不因此授予成员权限。

#### 文档完整读取与输入限制

query_docs 按路径返回完整正文，不再按 400 字符分页，不受通用工具结果裁剪或 context_max_bytes 本地输入长度限制。目录及搜索仍可翻页。仅真实的文档工具结果享受豁免，用户、网页和其他工具输入仍受限。实际输入 tokens 照常计入会话和每日预算，供应商上下文窗口仍适用；仅读取随插件提供且不超过 1 MiB 的 Markdown。

#### 命令条数与执行通知

`tools.execute_commands.max_commands_per_request` 控制群首轮或私聊本轮不同命令总数，默认 5，初始系统上限 100；失败计数，复用结果不重复计数。全局 Super 不受命令条数限制，但权限、群首轮资格、工具开关、调用次数、预算及超时仍生效。每批结束后由程序向用户发送执行记录，列出命令及成功、拒绝、未执行、结果未确认或复用状态；密钥参数脱敏。
