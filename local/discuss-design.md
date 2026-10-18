# 群内 AI 讨论功能设计

状态：v2.0.0-beta.1 设计与实现约定。本文记录已确认需求，并为未明确的行为给出可实施的默认方案。

## 1. 目标与边界

- 提供按群启用的轻量 AI 对话客户端，固定接入 DeepSeek 的 OpenAI 兼容 `/responses` 接口。
- 机器人只在用户 @ 机器人或回复机器人消息时处理对话，并在每次请求时校验本群 `group.discuss.user` 有效身份。
- 支持模型通过受控工具查询业务数据、搜索互联网、读取网页；不提供电脑控制、终端、任意代码执行、任意文件读写能力。
- 配置、权限、会话、预算和统计按群隔离，与已有总结、DDL 等功能分别管理。
- 全局 `super` 拥有最高管控权，任何群配置、名单或群管理员均不能撤销、阻断其管理权限。
- 按本方案实现，并使用 make publish 打包 v2.0.0-alpha.2；推送功能分支，不创建 Release。

## 2. 隔离范围

所有群数据的完整作用域为 `(platform, bot_id, group_id)`，防止多平台或多个机器人账号之间串用配置和凭据。

私聊命令必须明确目标群号，目标为接收该命令的机器人账号所在平台上的群。群聊身份组命令省略群号时只操作当前群，禁止借群聊操作其他群。

会话 ID、消息 ID、工具权限和统计查询都必须包含作用域校验，不能只凭一个外部传入的 ID 访问资源。

## 3. 权限模型

### 3.1 身份与职责

| 身份 | 范围 | 权限 |
| --- | --- | --- |
| 全局 `super` | 全部群 | 启停功能、任免群 discuss super/admin、管理 user 准入、查看和修改全部配置、查看统计、结束会话、管理系统全局上限 |
| `group.discuss.super` | 本群 | 继承本群 discuss admin 和 user 权限，增加或撤销本群 discuss admin |
| `group.discuss.admin` | 本群 | 继承本群 discuss user 权限，查看和设置群配置、管理 user 准入名单、查看群统计、管理本群会话 |
| 有效 `group.discuss.user` | 本群 | 触发 AI 对话、回复继续会话、查看和结束自己创建的会话 |

`group.discuss.super` 不能授予或撤销同级 super，也不能启用被全局 super 禁用的功能；群 super 的指定、更换和撤销由全局 super 完成。允许一群多个 discuss super；启用时至少指定一个。

现有全局 `admin`、`autoanalysis`、`group.admin` 以及 QQ 群主/管理员身份，不自动继承任何 discuss 管理能力。尤其不能沿用已有全员 `group.admin` 开关来授予 discuss 管理权限。

群内继承关系为 `group.discuss.super → group.discuss.admin → group.discuss.user`。有效群 discuss admin/super 自动拥有本群 user 身份，不受 whitelist/all/blacklist 模式或名单限制。全局 super 始终取得有效 user 身份；正常对话仍要求群功能已启用且预算足够。

### 3.2 全局 super 的最终控制权

- 管理鉴权首先识别全局 super，直接授予目标群所需的 discuss 管理权限；随后才计算群级角色。
- 黑名单、成员资格查询失败、群功能停用、预算耗尽和群级角色变化，不能阻止全局 super 的管理命令。
- 群 super/admin 不能修改全局 super 配置，也不能通过移除名单降低其有效权限。
- 全局 super 能接管任意群，替换群 super、撤销 admin、停用工具、替换凭据、结束会话。
- 所有可变全局 discuss 策略仅允许全局 super 管理。群级操作不能提高系统 config 的上限。
- 最高管控权通过确定性的管理命令实现，不通过提示词或授予 AI 电脑权限实现。
- 管理操作仍遵守位置规则：具体配置、统计和会话管理仅限私聊；身份组管理可私聊或群聊。Readonly 等既有全局机制保持生效，由全局 super 通过原有管理入口解除限制。

### 3.3 user 校验模式

管理员设置 `user_mode = whitelist | all | blacklist`，默认 `whitelist`。

| 模式 | 有效 `group.discuss.user` 判定 |
| --- | --- |
| `whitelist` | 本群成员且位于本群 user 白名单 |
| `all` | 本群全部成员 |
| `blacklist` | 本群成员且不在本群 user 黑名单 |

上述模式判定适用于没有继承 user 身份的普通用户；全局 super 及有效群 discuss admin/super 优先取得 user 身份，黑名单不覆盖继承授权。两个名单分别保存；切换模式不清空名单。`all` 模式下名单均不参与判定。白名单和黑名单允许包含同一用户，具体效果由当前模式决定。

`user add/remove` 明确表示授予/撤销白名单直接身份；`blacklist add/remove` 表示拉黑/解除拉黑，避免把“授予 user”解释成拒绝使用。移除 user 直接授权或加入黑名单不撤销 admin/super 继承的 user 权限，操作结果须明确提示。撤销管理身份后重新按剩余继承身份和当前准入模式计算，不额外保留继承所得 user 身份。身份查询同时展示直接授权、继承来源、当前模式和最终有效结果。

无 user 权限的普通对话触发静默忽略，不发起付费请求。显式管理命令走独立管理鉴权，不能因为缺少 user 身份而阻止管理员管理。

## 4. 消息触发与会话规则

1. 忽略机器人自身消息，依据平台消息 ID 持久化去重。
2. 先识别命令并按确定性命令路由执行；命令内容不作为 AI 问题。
3. 普通群消息仅在真实 at 段指向机器人，或真实 reply 段指向该机器人消息时，成为对话候选；文本伪造 @、昵称或 `@all` 不算。
4. 检查群功能、user 身份、Readonly、凭据、预算和并发限制，未通过不调用模型。
5. 回复本功能已登记的回答时延续对应会话；其他获准用户也能回复参与同一会话。
6. 单独 @ 默认新建会话。@ 且回复已有 discuss 回答时优先延续；@ 且引用其他消息时，把引用内容作为新会话材料。
7. 回复机器人其他功能的消息默认开新会话，将可取得的引用正文作为材料，不混入其他功能的内部历史。消息来源必须经可信平台数据核验，无法核验时不调用模型并提示使用 @。
8. 回复已结束会话只返回结束原因和“请重新 @ 开始新会话”，不能自动复活或静默新建。

群对话是群共享内容，不承诺参与者之间的私密性。每轮记录发言用户，避免压缩后混淆不同用户的需求；不读取整群聊天记录作为默认上下文。

### 4.1 生命周期

会话状态为 `active → closing → ended`；结束原因包括手动结束、并发会话淘汰、会话预算耗尽、管理员操作、功能停用。

- `max_sessions` 指群内活跃会话数，不是同时执行的网络请求数。
- 新建会话将超限时，按创建时间从早到晚结束旧会话，时间相同以会话 ID 排序。此处“之前的会话”采用最早创建定义，不采用最近活跃时间。
- 淘汰运行中的会话时立刻标记 closing，阻止新模型调用和工具执行；尽力取消在途请求，已有费用仍记账，迟到结果不再作为正常回答发送。
- 减小上限立即按同一规则淘汰；群关闭立即结束全部活跃会话，重新启用不恢复旧会话。
- 同一会话逐轮串行，群级预算和会话创建使用事务协调；不同会话可并行，但受系统并发上限控制。
- 一条用户请求包括其全部模型调用、工具循环和必要摘要；另设请求超时和模型请求轮数上限，避免无限循环。
- 每个回答消息 ID 映射到会话；映射和状态需持久化。发送结果不确定时不自动重发，也不重新执行整条 AI 请求。

## 5. 配置模型

群配置存储独立于既有模型配置；discuss 不回退使用总结功能的 API Key 或模型。

### 5.1 群配置

以下默认值为第一版建议，必须受系统 config 约束；未配置有效 API Key、模型时功能处于“已启用但未就绪”，不能付费调用。

| 配置键 | 建议默认 | 含义 / 全局约束 |
| --- | --- | --- |
| `enabled` | false | 仅全局 super 修改 |
| `max_sessions` | 5 | 活跃会话数；正整数，不超过系统最大值 |
| `session_token_budget` | 30000 | 单会话累计预算；正整数，不超过系统最大值 |
| `daily_token_budget` | 200000 | 群每日累计预算；正整数，不超过系统最大值 |
| `system_prompt` | 符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容 | 群系统提示词；继承系统默认，可由本群 admin 覆盖，字符数受系统上限约束 |
| `user_mode` | whitelist | 系统允许的模式集合之一 |
| `api_key` | 未设置 | 群独立密钥；长度/格式校验，查看仅脱敏 |
| `model_name` | 未设置 | 系统允许的 DeepSeek 模型名单之一 |
| `reasoning_effort` | 系统默认 | 系统允许且目标模型支持的枚举值 |
| `context_token_limit` | 6000 | 单次输入目标上限，受模型窗口和系统上限限制 |
| `summary_token_limit` | 600 | 历史摘要目标上限，不超过上下文上限 |
| `recent_turns` | 4 | 保留的最近完整对话轮数，仍受 token 上限限制 |
| `max_output_tokens` | 2048 | 单次模型输出上限，需包含接口定义下的思考输出预算 |
| `tools.<name>.enabled` | false | 该工具开关；系统禁用时群不能启用 |
| `tools.<name>.max_calls_per_request` | 3 | 同一用户请求中该工具实际执行次数上限，0 表示禁止 |
| `max_tool_calls_per_request` | 5 | 同一用户请求全部工具累计执行上限 |

### 5.2 系统 config

系统配置使用独立 `group_discuss` 命名空间，包含群默认值、各数值项最大值、工具全局开关、工具结果长度、模型允许名单、思考强度允许集合、请求时限、并发与队列限制、保留周期等。

“每项有全局上限”按类型解释：数值有最大值；枚举和模型名称有允许集合；工具开关有全局总开关；凭据有长度和格式约束。`enabled` 的控制者固定为全局 super，不用数值上限表达。

DeepSeek Responses 地址由系统配置确定，只允许全局 super 管理，群管理员不能设置供应商或任意 API 地址。若部署使用可信的 DeepSeek Responses 网关，地址由系统维护者提供，仍强制只允许 DeepSeek 模型。

不猜测供应商能力：上线前验证目标端点的 Responses 工具调用、usage、思考参数及输出上限语义；不自动回退到其他协议或其他供应商。

全局 super 可在私聊通过全局命令修改 discuss 系统配置；持久化到运行数据目录 group_discuss_policy.json，作为部署配置的明确覆盖层，重启后仍生效。

群设置超限直接拒绝并提示允许范围；展示页列出“存储值、当前生效值、系统约束”。系统上限收紧后立即重新计算生效值：数值取上限内的值，工具取开关交集；模型/模式等变为不允许时暂停相关请求并提示修正，不静默替换模型。

除 `enabled` 外，新增群参数若未显式设置则继承系统默认值；修改生效前校验参数间关系。改变凭据、模型或思考强度只影响后续模型调用，并保留每次调用的配置版本用于审计。

### 5.3 已确认的全局初始约束

| 群设置项 | 群默认 | 全局最大值 |
| --- | --- | --- |
| 活跃会话数 | 5 | 20 |
| 单会话累计 tokens | 30000 | 200000 |
| 单群每日 tokens | 200000 | 2000000 |
| 单次输入上下文 | 6000 | 24000 |
| 摘要 tokens | 600 | 2000 |
| 最近完整轮数 | 4 | 12 |
| 单次模型输出 tokens | 2048 | 8192 |
| 单工具每轮调用 | 3 | 8 |
| 全工具每轮调用 | 5 | 12 |

运行初始值：每轮总时限 180 秒、单模型调用 90 秒、每轮最多模型调用 8 次（包含摘要和重试）；单群并发 2、全局并发 6；单群等待 10、全局等待 30；工具超时 20 秒、单工具正文最多 3000 tokens、DeepSeek 工具响应最多 2 MiB（网页访问由 DeepSeek Fetch 服务完成）；正文保留 30 天。数值 token 预算采用 UTF-8 字节保守估算，实际计量以端点 usage 为准。

增加全机器人每日 token 总预算，初始 5000000；与各群每日预算同时预留和扣减，由全局 super 调整，不能通过增加群数绕过。按平台和机器人账号分别统计总预算。

工具系统总开关初始全部开启，各群默认仅开启 query_docs 文档查询，其余工具关闭。DeepSeek Responses 默认地址 https://api.deepseek.com；模型白名单默认包含 deepseek-v4-flash、deepseek-flash、deepseek-v4-pro、deepseek-pro，无需手动添加，群仍需配置自己的 Key 和模型，思考强度默认 low，以目标模型实际支持为前提。

### 5.4 查看与凭据保护

所有设置项均可由本群 discuss admin/super 和全局 super 在私聊查看，包括系统约束，但 API Key 永远不返回原文。

密钥统一显示为 `sk-XX*****XX`：保留去掉 `sk-` 后前两位和末两位，中间固定五个星号；非此前缀也使用统一展示格式。过短密钥完全隐藏，未配置显示“未设置”。设置成功不回显输入原文。

密钥不进入模型提示词、会话正文、工具参数、统计、审计变更正文或异常正文；修改审计只记录“已更新”和脱敏值。私聊接收消息的现有落盘链路也必须对设置 Key 命令脱敏，避免入口先保存原文。注册全部群当前和运行期见过的旧 Key 到统一出站及日志脱敏器。

运行必须保存可用凭据，采用独立受限凭据存储，不把 Key 存入通用配置导出或用量账本。凭据与历史采用 cryptography Fernet 加密；主密钥单独保存在 group_discuss.key，文件权限为 0600，不能放入数据库或 Git。备份必须包含主密钥文件。平台本身保留的私聊记录不由机器人控制。

## 6. Token 预算与上下文压缩

### 6.1 计费口径

- 会话预算和每日预算均累计实际模型 `input_tokens + output_tokens`，包括工具循环、摘要和重复发送历史的输入。
- 思考 tokens 若已包含在 output 中不重复相加；缓存输入仍计入 token 预算，折扣只影响费用估算。
- 搜索/Fetch 工具调用次数独立统计，费用按 DeepSeek 的工具计费规则由同群 Key 提供者承担；其结果送回模型产生的输入 tokens 纳入模型预算，token 预算不限制工具账单金额。
- 同一请求消耗同时记入会话和群当日账本，各记一次；工具循环中的每次模型调用有独立唯一请求 ID。
- 日界线固定 Asia/Shanghai 的 00:00；跨日请求按每次模型调用开始时的日期归账，实际返回时结算到原日期。
- 结束、删除会话或重启不能重置已用预算；每日额度耗尽后当日暂停新模型调用，次日可恢复尚未结束的会话。
- 单会话累计达到预算后自动结束。剩余额度不足安全发起下一次调用时，也结束该会话并标记预算不足；每日不足只暂停，不因此结束全部会话。

### 6.2 预留与结算

每次模型调用前在持久化事务中同时预留会话额度和当日额度。可用额度为 `预算 - 已确认消耗 - 未结算预留`，不能仅在响应后累加。

输入预估必须覆盖 system、历史、工具定义、当前工具链和协议开销，使用与端点匹配的计数能力；输出预留使用实际发送的输出上限，包含接口定义的思考输出。没有可靠的保守计数边界时，应明确展示“估算控制”，不能声称绝对不会超额。

响应后按 usage 结算并释放多余预留。失败、超时、取消或进程崩溃且不能确认未计费时，保留预留为“待确认消耗”，不能记为零或自动释放。支持全局 super 私聊人工核销，保留原因、操作者及差额审计，避免重试绕过预算。

默认关闭库内部的隐式付费重试；确需重试时作为新调用重新预留、单独记账。扣账与结算操作按请求 ID 幂等。

如果实际 usage 超过预留，记录全部实际消耗并立即阻止后续调用，不隐瞒超额。远端计量误差和不可中止的在途请求意味着客户端无法单方面保证供应商账单严格封顶；如需账单硬上限，须结合端点配额能力。

### 6.3 压缩策略

每次输入由短系统提示、滚动摘要、最近完整轮次、当前问题、必要引用以及当前工具链组成，不附带整群历史。

- 超过上下文预算时先裁剪历史工具返回，只保留必要字段、来源和结论；搜索先给少量摘要，按需读取正文。
- 保留最近完整轮次，较老记录达到阈值后才生成摘要，避免每轮总结反而增加费用。
- 摘要保存用户目标、参与者、约束、确认事实、关键原文数值和未解决事项；原始历史本地保留，以受控的本会话历史查询工具按需读取。
- 摘要本身属于该会话付费调用，遵守工具开关之外的同一 token 预算和额度预留；预算不足不继续总结。
- 当前未完成工具调用链及端点要求回传的思考/协议项不可随意截断。只在完整轮次边界压缩，不长期保存原始思考正文到普通日志或用户可读历史。
- 若当前问题和必要协议项本身超过安全上限，拒绝本次调用并请用户缩短；不得静默丢弃核心问题。
- 默认本地管理上下文、请求设置 `store=false`，不将 `previous_response_id` 误当成免费历史。目标端点有其他要求时先验证兼容性。

### 6.4 每轮回答的用量摘要

每轮对话完成后，由宿主程序在回答末尾附加本轮用量摘要，不由模型生成。这里“一轮”指一条用户请求及其完整处理过程，汇总该请求引发的全部模型调用，包括内部工具循环、必要的历史摘要及显式重试，不是只统计最后一次生成回答的调用，也不是整段会话的累计消耗。

固定展示输入 tokens、输出 tokens、缓存命中的输入 tokens，以及实际工具调用次数，例如：

```text
tokens input: 386(+128) output: 44. toolcall(s) 0.
```

- 输入和输出分别对本轮每次模型调用的 usage 求和；缓存命中取端点明确返回的 cached input tokens 并求和，是输入的子集，不再额外计入总消耗。
- 输出包含端点已计入 output 的思考 tokens，不重复累加。缓存字段缺失显示“未知”，不能假定为 0，也不按重复文本自行推算命中量。
- 工具次数按实际执行次数累计，覆盖本轮所有内部模型调用；一次模型响应发起三个工具执行计为三次。执行失败的调用也计数，授权或参数校验阶段已拦截、没有执行的调用不计入此数，另记拦截统计。
- 每轮通过唯一 turn_id 关联模型请求、工具执行和摘要调用，使用持久化账本聚合，防止重复回调造成重复计数；用量摘要本身不回传模型，不增加下一轮历史负担。
- 任一模型调用缺少完整 usage 时，对应指标显示“至少 N（另有未知）”；完全没有已知数值时显示“未知”。预留额度不是实际用量，不能作为精确 token 数输出。
- 有用户可见的超时、失败、预算中止等终止回复时，同样附加本轮已知用量并标明未知部分。未通过触发或准入检查而静默忽略的消息不发送用量摘要。
- 用量摘要只展示数值，不暴露密钥、内部工具参数或思考正文。若回答分成多条消息发送，摘要只在最后一条附加一次。

## 7. 工具边界

第一版工具建议分为 `search_web`、`fetch_webpage`、`query_group_data`、`read_session_history`。具体业务查询范围单独定义，默认关闭；新增 query_docs 只读项目文档查询默认开启。

工具只有在系统允许、群允许且未超过本请求对应上限和总上限时才可执行；每次执行前重新检查群开关、权限、会话状态和最新配置。模型输出一个工具调用不代表获准执行。

- `query_group_data` 仅使用固定只读查询接口，作用域和操作者由宿主程序注入，不接受模型指定任意群或任意 SQL。
- `read_session_history` 只读取当前会话，不允许指定其他会话绕过隔离。
- 网页 URL 只允许无认证的 HTTP(S)，拒绝本地 IP、localhost 等地址。Fetch 在 DeepSeek 服务端运行，DNS、重定向及实际连接的安全策略由供应商执行，本机不抓取网页。
- 限制响应大小、网页片段、超时、重定向次数和每次查询返回条数，不继承本机 cookies 或登录状态。
- 工具参数用显式 schema 校验。实际执行即占用次数，执行失败也计数；模型并行返回的调用必须逐个原子预占次数。
- 传给模型的工具描述只包含当前允许的工具。达到调用上限后返回简短受控结果，尝试在剩余预算内生成最终回答；模型轮数限制阻止反复请求已禁用工具。
- 网页、引用消息和工具结果均视为不可信内容，不能改变权限、导出密钥或调用管理命令。
- 不注册 shell、Python 执行器、桌面浏览器自动化、文件系统或任意 MCP 服务。未来新增工具需要明确能力边界。

Harness 使用 Pydantic AI 的 Responses 模型和工具循环，不自行实现 agent 循环、工具参数 schema 或对话消息序列化；使用支持 Python 3.10 的已验证依赖版本。无论采用何种库，授权、预算和审计必须保留在宿主程序控制边界，不依赖提示词实现。

## 8. 命令设计

所有功能命令使用 `/group-discuss`；全局 super 管理入口使用 `/super group-discuss`。不新增 `/query`、裸 `/discuss` 等别名。群 super/admin 分别使用 `/group-discuss super` 和 `/group-discuss admin` 子树。

`GROUP` 为群号，`USER` 为用户号；群聊身份组管理可省略 `GROUP` 表示本群，私聊必须填写。所有具体配置、统计和会话管理命令仅支持私聊，即使操作者是全局 super 也不在群聊显示这些数据。群聊身份命令沿用现有命令触发要求，需要 @ 机器人。

### 8.1 帮助与用户命令

| 命令 | 位置 | 说明 |
| --- | --- | --- |
| `/group-discuss help [主题]` | 私聊/群聊 | 独立帮助，按当前权限展示入口 |
| `/group-discuss role [GROUP]` | 私聊/群聊 | 查看本人本群身份来源和有效 user 状态；私聊指定群 |
| `/group-discuss sessions GROUP` | 私聊 | 查看自己创建的活跃会话 |
| `/group-discuss end GROUP SESSION` | 私聊 | 结束自己创建的会话 |

帮助属于静态管理信息，不触发模型；群未启用时仍可查看基础帮助。群配置、名单和统计不通过普通用户帮助泄漏。

### 8.2 全局 super 命令

| 命令 | 位置 | 说明 |
| --- | --- | --- |
| `/super group-discuss enable GROUP USER` | 私聊 | 启用功能并为 USER 增加群 discuss super；不清除原授权 |
| `/super group-discuss disable GROUP` | 私聊 | 停用并结束全部会话，保留配置和账本 |
| `/super group-discuss super add\|remove USER [GROUP]` | 私聊/群聊 | 任免群 discuss super |
| `/super group-discuss super list [GROUP]` | 私聊/群聊 | 查看本群 discuss super |
| `/super group-discuss admin add\|remove USER [GROUP]` | 私聊/群聊 | 直接任免群 discuss admin |
| `/super group-discuss config show GROUP` | 私聊 | 图片卡片展示群设置、来源和约束，Key 脱敏 |
| `/super group-discuss config set GROUP KEY VALUE` | 私聊 | 管理任意群配置，受系统上限约束 |
| `/super group-discuss limits show` | 私聊 | 查看全局默认、上限和允许集合 |
| `/super group-discuss limits set KEY VALUE` | 私聊 | 修改系统 discuss 配置并持久化 |
| `/super group-discuss stats GROUP [today\|YYYY-MM-DD\|all]` | 私聊 | 查看任意群统计 |
| `/super group-discuss sessions GROUP` | 私聊 | 查看任意群活跃会话 |
| `/super group-discuss end GROUP SESSION\|all` | 私聊 | 强制结束会话 |
| `/super group-discuss usage resolve GROUP REQUEST TOKENS REASON` | 私聊 | 核销未知消耗，完整审计，不删除原记录 |

全局 super 还可使用下列群 super/admin 子命令操作任意目标群，不依赖本群授权。角色管理不要求功能已启用，便于提前配置和接管。

### 8.3 群 discuss super 命令

| 命令 | 位置 | 说明 |
| --- | --- | --- |
| `/group-discuss super help` | 私聊/群聊 | 群 super 帮助 |
| `/group-discuss super admin add\|remove USER [GROUP]` | 私聊/群聊 | 增加或撤销本群 discuss admin |
| `/group-discuss super admin list [GROUP]` | 私聊/群聊 | 查看本群 discuss admin 直接名单及继承说明 |

移除直接 admin 不会取消仍存在的 discuss super 继承权限，结果应明确提示。最后一个群 super 的撤销仅由全局 super 完成；不会把群控制权转移给普通群管理员。

### 8.4 群 discuss admin 命令

| 命令 | 位置 | 说明 |
| --- | --- | --- |
| `/group-discuss admin help` | 私聊/群聊 | 管理帮助 |
| `/group-discuss admin config show GROUP [KEY]` | 仅私聊 | 图片卡片展示生效值、来源和系统约束；KEY 可选 |
| `/group-discuss admin config set GROUP KEY VALUE` | 仅私聊 | 设置配置，包括 user_mode、Key、模型、思考强度及各工具参数 |
| `/group-discuss admin config reset GROUP KEY` | 仅私聊 | 重置为系统默认；Key 重置为未设置；不重置用量 |
| `/group-discuss admin stats GROUP [today\|YYYY-MM-DD\|all]` | 仅私聊 | 群统计 |
| `/group-discuss admin sessions GROUP` | 仅私聊 | 本群活跃会话及预算状态 |
| `/group-discuss admin end GROUP SESSION\|all` | 仅私聊 | 结束本群会话 |
| `/group-discuss admin user add\|remove USER [GROUP]` | 私聊/群聊 | 维护 user 白名单 |
| `/group-discuss admin user list [GROUP]` | 私聊/群聊 | 查看白名单 |
| `/group-discuss admin blacklist add\|remove USER [GROUP]` | 私聊/群聊 | 维护 user 黑名单 |
| `/group-discuss admin blacklist list [GROUP]` | 私聊/群聊 | 查看黑名单 |
| `/group-discuss admin user show USER [GROUP]` | 私聊/群聊 | 查看指定用户的准入来源及有效状态 |

`user_mode` 是群具体配置，只能通过私聊 config 命令修改。身份名单命令可以群聊执行，群聊只显示本群身份数据，不附带 Key、预算或其他配置。

配置命令示例：

```text
/super group-discuss enable 123456 10001
/group-discuss super admin add 10002 123456
/group-discuss admin config set 123456 max_sessions 5
/group-discuss admin config set 123456 session_token_budget 30000
/group-discuss admin config set 123456 daily_token_budget 200000
/group-discuss admin config set 123456 user_mode whitelist
/group-discuss admin user add 10003 123456
/group-discuss admin config set 123456 api_key <密钥>
/group-discuss admin config set 123456 model_name <系统允许的DeepSeek模型>
/group-discuss admin config set 123456 reasoning_effort <该模型支持的强度>
/group-discuss admin config set 123456 tools.search_web.enabled true
/group-discuss admin config set 123456 tools.search_web.max_calls_per_request 2
```

命令解析固定 key 白名单和类型校验，不执行表达式。管理操作在真正写入前重新鉴权，防止排队期间权限已被撤销。

## 9. 统计与审计

群 admin/super 和全局 super 可在私聊查看：

- 功能就绪状态、活跃/已结束会话数量和结束原因。
- 请求数、成功/失败/中断/未知状态数量、参与人数。
- 输入、输出、总 tokens、缓存输入及思考 tokens 的可用明细。
- 当日与会话预算、已确认消耗、预留、待确认消耗和剩余额度。
- 按模型、用户、会话、日期汇总的 token 消耗；工具执行次数、错误及拦截次数。

思考和缓存明细只展示端点确实返回的值，缺失标记未知。token 统计不等同于人民币费用，外部工具收费也不混算。

配置、身份组、启停、强制结束和人工核销记录操作者、作用域、时间、变更与结果。普通统计不展示聊天全文、密钥和原始思考；会话列表只展示必要元数据。

## 10. 代码、存储与文档结构

沿用现有分层方式，在每层使用独立 `group_discuss` 子包：

```text
src/domain/group_discuss/             # 配置约束、权限规则、会话状态、预算规则
src/application/group_discuss/        # 触发、命令、配置管理、harness、压缩、统计
src/infrastructure/group_discuss/     # DeepSeek 客户端、工具实现、存储适配器
src/presentation/group_discuss/       # 帮助、设置与统计展示
docs/commands/group-discuss/                   # 独立命令文档子目录
  README.md                          # 功能入口、触发与会话语义
  help.md                            # /group-discuss help
  configuration.md                   # 群设置、默认值、系统约束
  roles.md                           # 身份与三种 user 模式
  super.md                           # /super group-discuss
  admin.md                           # /group-discuss admin
  tools.md                           # 工具与能力边界
  statistics.md                      # 预算与统计口径
local/discuss-design.md               # 本设计稿
```

现有入口只负责接入独立命令目录和消息分发，不把 discuss 实现堆入总结客户端或 DDL 服务。可复用消息网关、出站保护、身份存储基础设施和用量统计基础设施，但必须增加明确的 discuss scope/operation，避免重复扣账或跨功能混算。

运行数据放在现有插件数据目录，建议独立 `group_discuss.sqlite3` 保存群配置引用、会话、消息映射、历史/摘要、预算预留、模型调用、工具调用和管理审计；凭据存储独立。全局角色扩展如复用 roles 存储，必须同步更新角色校验、继承、解析及迁移，不能仅增加字符串常量。

数据库中的预算预留与结算为预算判断的唯一事实来源。若复用现有 `usage.sqlite3` 展示全局统计，以唯一 request_id 幂等投影或在统一事务数据库内保存，不依赖两个数据库的非原子双写保证额度。

启动恢复 active 会话和消息映射，未完成请求记为 interrupted/unknown，保留预留且不自动重放；closing 会话完成结束处理。历史保留和清理有系统上限，清理正文不能删除预算账本、必要审计或改变额度。

## 11. 兼容、迁移与验收

新增功能默认对所有群关闭，不复用旧群角色或旧模型凭据自动开放能力。迁移必须备份、事务执行并校验；失败不能清空旧数据重新创建。

实现后变更仅写 CHANGELOG 顶部 `# Dev`，不修改已发布版本内容；同步简短更新 `src/UPDATE.md`，旧版迁移后的更新公告沿用现有 announce 接收条件及发送机制。用户明确要求发布具体版本时，使用 `make publish` 生成完整发布内容。本次 v2.0.0-alpha.1 已将 Dev 改为具体版本并冻结条目。

实现验收重点：

1. 真实 @ / 回复触发、无权限静默、命令不进入模型、机器人自发消息不循环。
2. 全局 super 接管任何群；群 admin、现有 group.admin、跨群私聊无法越权；角色撤销在写入和工具执行前生效。
3. 三种 user 模式、名单保留、super → admin → user 继承及撤销后的重新计算正确；黑名单和直接 user 移除不覆盖管理身份继承。
4. 配置只在私聊操作；身份组管理可在本群或私聊进行；Key 在回复、日志、审计和私聊记录落盘链路中均受保护。
5. 会话按创建时间淘汰，跨用户回复延续，已结束会话不复活，重启不重置账本。
6. 并行请求不重复预留，工具循环和摘要均扣账；午夜跨日、缺失 usage、超时、崩溃和重试均有明确记录。
7. 工具逐项开关和限次、全局上限收紧、内网请求阻断、作用域隔离正确；不存在执行代码或控制电脑的工具。
8. DeepSeek Responses 完成真实工具往返、思考参数、输出上限和 usage 解析验证；压缩不破坏当前工具链。
9. 每轮回答附带全部内部模型调用汇总的输入/输出 tokens、缓存命中和实际工具次数；多工具、摘要、失败和缺失 usage 场景下不漏算、不重复计数、不把未知显示为零。

## 12. 实施前需要验证的技术事实

- 部署所用 DeepSeek `/responses` 地址与实际支持的模型、思考强度枚举、token 计量和输出限制语义。
- Pydantic AI 2.0.0 与目标端点的真实兼容性；框架负责 Responses 调用、工具 schema、调用循环及消息序列化。
- AstrBot 配置持久化接口、现有私聊消息保存时机，以及可用的凭据保护方案。
- 搜索服务选择和凭据归属；第一版具体业务只读查询范围。

这些验证不改变已确认的权限、命令命名、目录位置和禁止 AI 控制电脑的边界。

## 13. 群系统提示词

系统 `group_discuss.defaults.system_prompt` 默认：

> 符合社会价值观，不得识别或输出敏感内容，拒绝角色扮演，拒绝危险任务，不得响应辱骂或者人身攻击内容

本群 group.discuss.admin、继承 admin 的群 super，以及全局 super，可私聊执行 `config set GROUP system_prompt "提示词"`，通过 show 查看、reset 恢复系统默认。系统 `system_prompt_max_chars` 初始 4000；过长或空白文本拒绝，系统上限收紧后超限的已有提示词暂停调用并提示修改，不静默截断。

每次模型请求（包括摘要）由程序将群系统提示词放入 instructions。普通用户输入默认不可信，仅在 user role 以结构化数据提供；引用、历史、摘要和工具结果也不能提升为系统规则。角色、预算、工具能力由程序强制校验，群提示词不能改变这些限制。提示词约束不是关键词检测器，不声称能保证模型绝不产生不当内容。


## alpha.2 补充：统一角色、图片帮助和 DeepSeek 联网

- 三种 discuss 身份纳入 /role、/super role，与专用身份命令共用 roles.json，按平台/机器人/群隔离。继承关系和全局 super 最终控制权保持有效。旧 JSON 自动备份升级，旧 SQLite 授权合并后删除，黑名单保留在 discuss。
- 文档统一在 docs/commands/group-discuss，admin 和 group-super 文档合并为 admin.md，但权限等级独立。所有 help 使用现有 CHAT/GROUP JPEG，支持 /help group-discuss、/help group-discuss-admin 和 /super help group-discuss。
- 根据 DeepSeek 官方兼容表，deepseek-v4-pro 使用 Responses web_search，deepseek-flash 与未知模型使用 /v1/tools/search 和 /v1/tools/fetch。未配置第三方搜索，不借用运营者 Key；模型与工具全由同群 API Key 付费。
- 内置搜索包含网页访问，只有 search_web/fetch_webpage 两者都启用且有剩余额度时注册。官方忽略 max_tool_calls，响应内可能越过次数上限，只能记录返回动作并阻止后续调用；独立接口逐次执行前硬限次。
- 每轮 summary 输出实际搜索/网页来源：内置、外置（DeepSeek 独立接口）、两者或未使用，不将工具计费伪装成模型 token。
- 本次使用 make publish 打包 v2.0.0-alpha.2，commit 和 push，不创建 GitHub Release/pre-release；旧版 changelog 不变。


## alpha.3 补充：配置卡片与文档渲染

- config show 在私聊返回图片卡片，支持全量或单项设置，显示生效值、配置来源、受限存储值和相关系统约束，密钥只传递脱敏值给渲染器。
- 默认模型白名单包含 deepseek-v4-flash、deepseek-flash、deepseek-v4-pro、deepseek-pro；不覆盖已有显式白名单。
- 配置指南以新手常用设置开头，完整列出群与全局设置；四至六级标题保留在父卡片内，表格保留命令高亮与转义竖线。
- 本次使用 make publish 打包 v2.0.0-alpha.3，支持从 alpha.1/alpha.2 升级并沿用自动更新公告。


## beta.1 发布约定

- /role 使用与群配置共用的本地图片布局，按全局及群展示权限来源；私聊显示编码，群聊只显示当前群，群较多时分图。
- 分阶段提交渲染修复、功能实现与版本准备；使用 make publish 打包 v2.0.0-beta.1，推送功能分支和版本标签，发布 GitHub pre-release，不并入主分支。
- 支持从 alpha.1/alpha.2/alpha.3 升级，保留历史数据和公告机制；已编号 CHANGELOG 条目不修改。


## beta.1.1：简洁用量与文档查询技能

- 用量首行固定为 tokens input: 386(+128) output: 44. toolcall(s) 0.；括号中的缓存属于 input 子集，搜索/网页来源仍单列。
- query_docs 提供目录、关键词搜索和按 path/offset 分页读取，只允许随插件提供的 docs Markdown，无任意文件读取或执行能力。默认系统及每群开启，单工具默认 3 次/请求，初始系统上限 8 次，受权限、预算和总工具次数约束。
- 旧全局配置自动补齐文档工具设置，保留已显式关闭的配置。
- make publish 打包 v2.0.0-beta.1.1，commit 并 push 功能分支，不推送标签、不创建 GitHub Release/pre-release。
