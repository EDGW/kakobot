# 个人 AI 对话 Super 管理 命令组

[命令目录](../README.md) · [个人 AI 对话](README.md) · [配置](configuration.md) · [Super 目录](../super/README.md)

本组涉及以下身份组：

- `super`：仅全局 Super；群管理员或群 discuss 管理员不具备个人用户管理权。

本页实际管理命令仅限私聊，作用于当前平台与机器人。个人用户无需新增身份组；全局 Super 默认开放，其他用户默认关闭，显式 disable 覆盖默认开放。所有用户均须自备 DeepSeek Key。

## `/super discuss help` 命令

### `/super discuss help` - CHAT

**完整格式**：`/super discuss help`；`/super discuss` 无参数同义。

**所需权限组**：`super`

发送本页 JPEG，与 `/super help discuss` 相同。读取和发送前验证全局 Super 身份；群内只可通过 `/super help discuss` 查看静态不可用说明。

```text
/super discuss help
/super help discuss
```

## `/super discuss switch` 命令

### `/super discuss switch` - CHAT

**完整格式**：`/super discuss switch true|false|reset`

**所需权限组**：`super`

true、false 持久化覆盖个人总开关；reset 删除命令覆盖并恢复部署配置 discuss.enabled，初始 true。关闭时结束全部个人会话，包括 Super 的会话；不关闭群 discuss。部署总开关和命令覆盖均可查看，无须配置全局 AI Key。

```text
/super discuss switch false
/super discuss switch true
/super discuss switch reset
```

## `/super discuss enable` 与 `/super discuss disable` 命令

### `/super discuss enable` - CHAT

**完整格式**：`/super discuss enable USER`

**所需权限组**：`super`

为目标用户开启个人 discuss。总开关仍须开启，用户还须设置自己的 Key；不授予 ddl 等业务身份。对全局 Super 通常无需执行，除非此前被显式关闭。

```text
/super discuss enable 123456
```

### `/super discuss disable` - CHAT

**完整格式**：`/super discuss disable USER`

**所需权限组**：`super`

显式关闭用户开放开关，结束该用户全部个人会话并尝试取消在途请求，后续工具循环重新检查。Key 与已用额度保留，不影响群 discuss 准入。

```text
/super discuss disable 123456
```

## `/super discuss users` 命令

### `/super discuss users` - CHAT

**完整格式**：`/super discuss users`

**所需权限组**：`super`

查看当前平台、机器人下已保存个人配置的用户及开放开关、Key 掩码。默认开放但尚无个人记录的 Super 不列入此名单；可用 `/discuss status` 查看自身生效状态。

```text
/super discuss users
```

## `/super discuss config` 命令

### `/super discuss config show` - CHAT

**完整格式**：`/super discuss config show USER [KEY]`

**所需权限组**：`super`

发送目标用户当前生效配置卡片，可指定单项。展示用户开放状态、脱敏 Key、模型、思考强度、预算和工具权限，标注系统默认、用户覆盖及全局约束。总开关另外通过 limits show 查看。

```text
/super discuss config show 123456
/super discuss config show 123456 api_key
```

### `/super discuss config set` - CHAT

**完整格式**：`/super discuss config set USER KEY VALUE`

**所需权限组**：`super`

修改单个用户配置，数值不能超过系统 maxima，工具开关不能突破全局 tool_enabled。支持模型、思考强度、个人系统提示词、会话/每日预算、上下文 bytes 与工具限次，完整字段见 [个人配置](configuration.md)。含空格的值使用英文双引号，布尔值使用 true 或 false。

不接受 user_mode、max_sessions 和群查询工具配置。Super 不代用户设置 Key；用户通过私聊 `/discuss apikey = KEY` 自行设置。通过 AI 调用业务命令仍需用户有原权限。

```text
/super discuss config set 123456 model_name deepseek-v4-flash
/super discuss config set 123456 reasoning_effort medium
/super discuss config set 123456 daily_token_budget 2000000
/super discuss config set 123456 tools.execute_commands.enabled true
/super discuss config set 123456 system_prompt "简洁回答，拒绝危险任务，包含公式时使用卡片。"
```

### `/super discuss config reset` - CHAT

**完整格式**：`/super discuss config reset USER KEY`

**所需权限组**：`super`

删除用户单项覆盖并恢复通用默认值。reset api_key 清除目标用户 Key 并结束其个人会话，不恢复为运营者或群 Key。

```text
/super discuss config reset 123456 reasoning_effort
/super discuss config reset 123456 api_key
```

## `/super discuss sessions` 与 `/super discuss end` 命令

### `/super discuss sessions` - CHAT

**完整格式**：`/super discuss sessions USER`

**所需权限组**：`super`

查看目标用户的活动个人会话 ID。每用户每机器人仅保留一个活动个人会话；群会话单独管理。

```text
/super discuss sessions 123456
```

### `/super discuss end` - CHAT

**完整格式**：`/super discuss end USER SESSION|all`

**所需权限组**：`super`

结束指定个人会话或该用户全部个人会话。SESSION 必须属于目标用户的当前平台与机器人；其他用户或群会话 ID 会被拒绝。结束不清零已用额度。

```text
/super discuss end 123456 all
```

## `/super discuss statistics` 命令

### `/super discuss statistics` - CHAT

**完整格式**：`/super discuss statistics USER [today|all|YYYY-MM-DD]`；stats 是同义入口。

**所需权限组**：`super`

查看用户输入、输出、缓存及按模型、会话、日期、状态、操作者拆分的统计，并附当前预算。默认 today，按北京时间统计；与群统计分开，机器人全局每日额度由个人和群请求共用。统计不展示 Key 或对话正文。

```text
/super discuss statistics 123456
/super discuss statistics 123456 all
```

## `/super discuss limits` 命令

### `/super discuss limits show` - CHAT

**完整格式**：`/super discuss limits show`

**所需权限组**：`super`

展示个人总开关和完整共用系统策略。个人入口新增部署配置仅 discuss.enabled，其余模型白名单、通用默认值、最大上限、全局工具门禁、并发与全局每日额度均复用已有 discuss 策略。

```text
/super discuss limits show
```

### `/super discuss limits set` - CHAT

**完整格式**：`/super discuss limits set KEY VALUE`

**所需权限组**：`super`

修改共用系统策略，个人与群 discuss 都实时生效。KEY 不带 group_discuss 前缀；defaults.KEY、maxima.KEY、tool_enabled.TOOL 使用点号。修改前确认对已有群的影响。个人独立总开关请用 switch，不使用 limits set enabled。

```text
/super discuss limits set tool_enabled.execute_commands false
/super discuss limits set maxima.daily_token_budget 20000000
```

## `/super discuss usage resolve` 命令

### `/super discuss usage resolve` - CHAT

**完整格式**：`/super discuss usage resolve USER CALL_ID TOKENS REASON`

**所需权限组**：`super`

核销目标用户结果未知的模型用量，TOKENS 为核实后的非负整数。只处理目标用户当前作用域中的 CALL_ID；保留原用量与差额审计。供应商独立 Search/Fetch 的费用不能换算为已知模型 tokens。

```text
/super discuss usage resolve 123456 CALL_ID 1200 "根据供应商记录核实"
```
