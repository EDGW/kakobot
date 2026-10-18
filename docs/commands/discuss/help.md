# 个人 AI 对话帮助与会话 命令组

[命令目录](../README.md) · [个人 AI 对话](README.md) · [配置](configuration.md) · [Super 管理](super.md)

本组涉及以下身份组：

- 无：查看帮助、查看和清除本人 Key、查看状态、结束本人会话。
- 全局 Super 默认开放个人 discuss；其他用户须由 Super 开放，无需新增身份组。
- 通过 AI 执行业务命令时，仍须具备原命令要求的身份组，例如私聊创建 DDL 需要 `ddl`。

本页所有实际对话、Key 和会话命令仅限私聊。`/help discuss` 可以在群内查看不可用说明，不会开启群内个人对话。模型与联网请求仅使用当前用户自己的 DeepSeek Key。

## `/discuss help` 命令

### `/discuss help` - CHAT

**完整格式**：`/discuss help [help|tools|configuration]`

**所需权限组**：无；查看说明不要求开放个人 discuss。

发送当前主题的 JPEG；不带主题时发送本页，与 `/help discuss` 相同。其他专题分别对应 `/help discuss-tools` 和 `/help discuss-configuration`。帮助图片按 CHAT/GROUP 区分，不按用户权限删减；查看文档不代表具备执行权限。

```text
/discuss help
/discuss help tools
/discuss help configuration
```

## `/discuss apikey` 命令

### `/discuss apikey` - CHAT

**完整格式**：`/discuss apikey = KEY`、`/discuss apikey show`、`/discuss apikey clear`

**所需权限组**：无；设置时须总开关开启且本人已获开放，查看与清除不受开放状态限制。

KEY 为 8～512 字符，不得包含空白。程序直接解析并加密保存，设置消息不进入模型上下文，成功提示不回显 Key。show 仅显示 `sk-XX*****XX`；clear 删除 Key。更换或清除 Key 会结束个人会话，避免跨 Key 延续。设置成功时提示普通私聊改由 discuss 接管，并说明业务命令工具可代替 DDL 自动分析；移除 Key 后恢复原有 autoanalysis 分发（仍须满足原权限与开关）。已观察过的旧 Key 在本次运行期继续受到出站保护。

即使用户是 Super，也不使用全局 AI Key 或群 Key；Key 未配置、失效或余额不足时直接报错，不自动切换。用户付清自己的模型与联网费用。

```text
/discuss apikey = sk-REPLACE-WITH-YOUR-KEY
/discuss apikey show
/discuss apikey clear
```

## `/discuss` 命令

### `/discuss` - CHAT

**完整格式**：`/discuss 问题内容`；无参数时发送帮助图片。

**所需权限组**：无；须总开关开启、本人已获开放并配置个人 Key。

没有活动会话时自动新建，否则延续当前个人会话；每人每个机器人仅一个活动个人会话。回复已记录的个人 discuss 回答，也可延续对应会话。本人已获开放且设置个人 Key 后，普通私聊文字也自动进入 discuss，不再进入 autoanalysis；无需逐句添加 /discuss。每句话加入当前会话上下文，直到 /new、新建或结束会话；触发压缩时保留摘要继续对话。其他业务斜线命令仍走原命令入口。

每轮附 `tokens input: N(+cached) output: N. toolcall(s) N.` 和搜索来源。长文、表格和公式渲染为 Markdown 卡片，包含 LaTeX、代码高亮与列表；AI 可主动选用渲染器。卡片中的链接另外发送合并聊天记录；渲染失败退回文字。

```text
/discuss 用三句话解释什么是反向传播
```

## `/discuss new` 命令

### `/discuss new` - CHAT

**完整格式**：`/new [问题内容]` 或 `/discuss new [问题内容]`

**所需权限组**：无；须本人已获开放，总开关与个人 Key 均有效。

结束旧会话；带问题时立即建立新会话，不带问题时由下一条普通私聊建立新会话，均不携带旧历史。已发生的每日用量保留，不通过新建清空额度。

```text
/new
/new 帮我安排今天的学习计划
```

## `/discuss end` 命令

### `/discuss end` - CHAT

**完整格式**：`/discuss end`

**所需权限组**：无；仅结束本人会话。

结束当前个人会话，尝试取消在途请求；已发生或未确认的用量保留。下一次 `/discuss 内容` 新建会话。引用已结束会话的消息不会恢复该会话。

```text
/discuss end
```

## `/discuss status` 命令

### `/discuss status` - CHAT

**完整格式**：`/discuss status`

**所需权限组**：无；仅查看本人。

发送本人配置卡片和预算信息，包含用户开放状态、脱敏 Key、模型、思考强度、可用工具、每会话及每日额度。总开关单独显示，用户开关开启并不代表总开关已开启。具体配置由 Super 管理，用户只能设置自己的 Key。

```text
/discuss status
```

## 会话、压缩与关闭

#### 压缩

下一轮开始前，历史投影超过上下文字节上限的 75% 时，使用个人 Key 将较旧对话压缩为摘要，并优先保留最近轮次。完整历史仍加密归档；压缩不关闭会话，也不清零预算。单轮必要上下文超过字节上限时返回限制提示。

#### 关闭与暂停

会话 token 预算耗尽、新建会话、手动结束、更换或清除 Key、Super 关闭用户或关闭总开关时结束会话；每日额度不足则暂停请求，次日可继续尚未结束的会话。私聊业务命令每轮均可用，但仍须用户工具开关和原命令权限均允许；详见 [工具说明](tools.md)。
