# 群 AI 对话帮助与会话 命令组

[命令目录](../README.md) · [群 AI 对话](README.md) · [Super 管理](../super/README.md)

本组涉及以下身份组：

- 无：查看帮助和本人身份。
- `group.discuss.user`：发起对话，查看和结束自己创建的会话。
- `group.discuss.admin`：继承 user；群 super 继承 admin。

真实 @ 机器人新建会话，回复机器人的 discuss 回答继续原会话。无有效 user 权限时静默忽略。会话超限按创建时间淘汰，会话预算不足自动结束，每日额度不足暂停；上下文压缩不清零消耗。每轮附输入、输出、缓存命中、工具次数及搜索来源。

## `/group-discuss help` 命令

### `/group-discuss help` - CHAT

**完整格式**：`/group-discuss help [help|admin|roles|tools|configuration|statistics]`

**所需权限组**：无；所有用户可用。

发送当前私聊对应的群 AI 帮助 JPEG。省略主题时发送本页；指定主题时发送该主题完整文档图片。

| 主题 | 用法 | 内容 |
| --- | --- | --- |
| help | `/group-discuss help` 或 `/group-discuss help help` | 当前帮助页和自己的会话管理 |
| admin | `/group-discuss help admin` | 群 admin 与群 super 共用管理帮助 |
| roles | `/group-discuss help roles` | 角色继承、统一身份管理与用户准入 |
| tools | `/group-discuss help tools` | 工具权限、联网能力与费用归属 |
| configuration | `/group-discuss help configuration` | 群配置、默认值与系统约束 |
| statistics | `/group-discuss help statistics` | 预算、用量、压缩与统计 |

`/help group-discuss` 发送本页；其他主题也可通过 `/help group-discuss-主题` 查看。`/group-discuss admin help` 与 `/group-discuss super help` 共用 admin 管理卡片，group-super 是 admin 主题别名；全局管理帮助使用 `/super help group-discuss`，须全局 super。

图片按 CHAT/GROUP 选择，不按个人身份组裁剪；能查看帮助不代表拥有执行权限。只接受一个主题，不支持继续追加子命令。不存在的主题返回提示，缺失或损坏的图片提示重新构建，不回退文字帮助。图片只发送到当前会话。

```text
/group-discuss help
/group-discuss help admin
/group-discuss help tools
```

### `/group-discuss help` - GROUP

**完整格式**：`/group-discuss help [help|admin|roles|tools]`

**所需权限组**：无；所有用户可用。

发送当前群聊对应的群 AI 帮助 JPEG。省略主题时发送本页；指定主题时发送该主题完整文档图片。

| 主题 | 用法 | 内容 |
| --- | --- | --- |
| help | `/group-discuss help` 或 `/group-discuss help help` | 当前帮助页和自己的会话管理 |
| admin | `/group-discuss help admin` | 群 admin 与群 super 共用管理帮助 |
| roles | `/group-discuss help roles` | 角色继承、统一身份管理与用户准入 |
| tools | `/group-discuss help tools` | 工具权限、联网能力与费用归属 |

`/help group-discuss` 发送本页；其他主题也可通过 `/help group-discuss-主题` 查看。`/group-discuss admin help` 与 `/group-discuss super help` 共用 admin 管理卡片，group-super 是 admin 主题别名；全局管理帮助使用 `/super help group-discuss`，须全局 super。

图片按 CHAT/GROUP 选择，不按个人身份组裁剪；能查看帮助不代表拥有执行权限。只接受一个主题，不支持继续追加子命令。不存在的主题返回提示，缺失或损坏的图片提示重新构建，不回退文字帮助。图片只发送到当前会话。

群内需 @ 机器人。配置与统计专题请私聊查看；`/help group-discuss-configuration` 和 `/help group-discuss-statistics` 可查看静态说明，实际配置与统计操作仅限私聊。

```text
/group-discuss help
/group-discuss help admin
/group-discuss help tools
```

## `/group-discuss role` 命令

### `/group-discuss role` - CHAT

**完整格式**：`/group-discuss role GROUP`

**所需权限组**：无；仅查看本人。

查看本人本群 discuss 身份及 user 准入。私聊必须指定群号；也可通过 `/role` 查看统一角色与来源。

```text
/group-discuss role 123456
```

### `/group-discuss role` - GROUP

**完整格式**：`/group-discuss role`

**所需权限组**：无；仅查看本人。

查看本人当前群的 discuss 身份及 user 准入，也可通过 `/role` 查看统一角色与来源。

群内需 @ 机器人；只查看当前群，不接受额外群号。

```text
/group-discuss role
```

## `/group-discuss sessions` 命令

### `/group-discuss sessions` - CHAT

**完整格式**：`/group-discuss sessions GROUP`

**所需权限组**：有效 `group.discuss.user`

仅列出自己创建的活跃会话。

```text
/group-discuss sessions 123456
```

### `/group-discuss sessions` - GROUP

**完整格式**：`/group-discuss sessions GROUP`

**所需权限组**：有效 `group.discuss.user`

当前位置不可执行；请私聊机器人并明确目标群号。

## `/group-discuss end` 命令

### `/group-discuss end` - CHAT

**完整格式**：`/group-discuss end GROUP SESSION`

**所需权限组**：有效 `group.discuss.user`

只能结束自己创建的会话，不能使用 all。

```text
/group-discuss end 123456 SESSION
```

### `/group-discuss end` - GROUP

**完整格式**：`/group-discuss end GROUP SESSION`

**所需权限组**：有效 `group.discuss.user`

当前位置不可执行；请私聊机器人并明确目标群号。

## 回答与卡片输出

简短回答通常发送文字，AI 可以选择紧凑 Markdown 卡片。超过 1000 字符、含数学公式或 Markdown 表格时自动使用卡片，优先按文本行、表格行及公式边界分页；回复任一页图片都能继续原会话。用量统计和来源放在正文后的卡片底部。

支持 CommonMark Markdown 以及表格、删除线、任务列表、脚注、定义列表和代码语法高亮；公式由 KaTeX 排版，支持 $...$、$$...$$、\(...\) 和 \[...\]，以及常用矩阵、积分等 LaTeX 数学语法。KaTeX 不等于完整 TeX 文档编译器，未支持的公式会显示错误原文；不执行原始 HTML、脚本或加载远程图片，图片仅显示替代文字。图片中的链接会额外汇总为合并聊天记录，保留标题、去重并可点击；回复该记录也能继续原会话。普通文字回答不重复发送链接记录。

本地渲染最多 60000 字符、总高 40000 像素，每页最多 1800 像素，并发 2、超时 30 秒；没有浏览器或超出渲染限制时自动退回文字。Playwright Chromium 和系统依赖均需管理员手动安装，插件不会自动下载、安装或更新浏览器，具体参见项目 README。

## blacklist 模式的违规警告

仅在 blacklist 模式下，AI 明确判定当前用户要求违反本群系统规则时，机器人会拒绝并发出一次警告。同一用户在本群收到警告后，24 小时内再次提出同类违规要求，自动加入本群 discuss 黑名单，并在群内告知用户编号和原因。重新 @、开启新会话或重启不会清除有效警告；不同用户、不同群、不同违规类别分别计算。

仅本群 group.discuss.admin、继承它的 group.discuss.super 及全局 Super 豁免自动警告与拉黑，但违规请求仍会被拒绝。group.admin（包括继承）及全员 group.ddl 模式不豁免。

模糊问题应先澄清，正常询问规则、引用材料、工具故障及预算不足不属于违规。仅成功发出的明确警告计入；失败的模型请求或发送不执行自动处罚。AI 提供违规类别，由宿主核验当前用户、群模式、权限和已送达警告，再决定操作，不允许 AI 指定其他用户。

管理员可查看或撤销黑名单；撤销时清除该用户在本群的警告：

```text
/group-discuss admin blacklist list 123456
/group-discuss admin blacklist remove 10003 123456
```

模型判断可能有误，管理员可按上述命令纠正；操作保留审计记录，不重复传播违规原文。


## 文档与自动执行

向用户解释规则时读取 `docs/` 用户文档（query_docs 的 audience=user）；自动执行时读取从同一来源生成的 `docs-bot/` 精简文档（audience=bot）。Bot 文档去重重复段落，保留全部内容、CHAT/GROUP 范围、权限、参数和示例；blocks-v1 中 order 的数字引用 blocks 下标，字符串直接连接，可还原原文。支持 paths 一次读取最多8篇独立文档；同轮相同内容不重复返回。

文档全文在当前轮内可用且照常计入实际 tokens；跨轮仅发送路径、内容哈希和简短摘录，结论保留于对话，需要完整规则时重新读取。完整工具记录仍归档。摘要触发按实际跨轮投影计算，阈值和最近轮数沿用原配置。

明确且独立的业务操作合并为 commands 列表，按顺序执行并逐条校验；缺少参数先询问。自动创建 DDL 优先使用 `/ddl add`，由原有 AI 流程提取用户需求；也允许使用 `/ddl add-strict` 结构化创建。通知对象写在末尾 `;@QQ号` 或 `;<at@昵称:QQ号>`，支持逗号分隔；只允许当前群成员，私聊只通知本人。使用 add-strict 且需要到期提醒时明确加入 `-0min`；add 默认追加到期提醒，用户明确取消时除外。

每次模型请求（含摘要、业务内部 AI）附程序生成的北京时间、时区和 Unix 时间戳。群聊用户真实 @ 转为 `<at@昵称:QQ号>` 发给 AI；AI 输出该标记时按当前群成员身份转换为真实 @。代码示例中的标记保持文字，图片回答附带真实 @ 消息；无法核验时只发送文字，不通知未知成员。

用量的缓存命中包含在输入内，不额外相加；显示本轮模型请求数、对话/摘要/业务内部 AI 的请求数与输入输出。未知用量单独显示预算预留，预留不代表实际用量；历史调用可能标为未分类。

execute_commands 的工具参数未通过校验时，不执行该调用，并将脱敏后的字段、类型原因反馈给 AI，允许修正一次；再次失败结束本轮并报告原因。已执行命令沿用持久化去重，不随参数纠错重复执行；纠错请求照常计入用量、模型次数及预算，业务拒绝或执行结果不确定不会因此自动重试。诊断不保留原始参数。


## AI 创建 DDL 时传递成员提及

自动执行 `/ddl add` 时，群成员使用 `<at@昵称:QQ号>` 标记；程序将标记转换为真实 @ 组件后交给原有 DDL 流程，QQ 号必须是当前群成员，昵称仅作展示。不要把正文提及写成普通 `@昵称` 或 `@QQ号`，这类纯文字不会增加通知对象候选。多个提及各写一个标记；未知 QQ 号先询问，不编造。

按语义决定哪些被提及的人需要通知时，把标记写在正文里。仅被提及不等于必须通知，例如“负责审核”“不要提醒”的成员由提取模型按完整语义判断：

```json
{"commands":["/ddl add 提醒<at@小明:12345678>和<at@小红:23456789>明天18点提交作业，提前30分钟提醒"]}
```

已经明确收件人时，优先使用末尾 `;<at@昵称:QQ号>`，多名成员用英文逗号分隔；后缀表示收件人限定，提取结果必须与其一致，否则拒绝创建：

```json
{"commands":["/ddl add 明天18点提交作业，提前30分钟提醒;<at@小明:12345678>,<at@小红:23456789>"]}
```

上述号码仅为格式示例，执行时必须替换成当前群已核验成员。私聊创建只通知本人，不接受其他通知对象。创建结果以工具返回为准，未确认成功前不能声称已经设置提醒；不因对象识别失败擅自改为通知发起人。
