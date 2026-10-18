# discuss 用量与统计

每轮回答附带程序生成的用量摘要：

```text
tokens input: 386(+128) output: 44. toolcall(s) 0.
搜索/网页来源：未使用。
```

input 为本轮全部输入，括号 (+128) 标注其中的缓存命中子集，不是额外增加的输入。汇总该用户请求的全部模型调用，包括内部工具循环和摘要。缓存命中属于输入子集，不额外累加；思考已包含在输出时不重复计数。实际执行失败的工具计入次数；执行前被拦截的不计。缺失 usage 显示未知，部分已知显示“至少 N（另有未知）”。

管理员仅可私聊查询：

```text
/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]
/group-discuss admin sessions GROUP
```

预算累计输入与输出，包括重复历史、缓存输入及摘要。日界线为 Asia/Shanghai 00:00，每次模型调用按开始日期归账。每次调用同时预留会话、群当日与机器人当日额度，得到 usage 后按实际结算；超时、崩溃或缺失 usage 保留预留，不能按零处理。

输入以 UTF-8 字节和协议余量保守估算，可能比实际 tokens 提前拒绝；实际计量以端点为准，客户端不能单方面保证供应商账单绝对封顶。全局 super 可核实账单后人工核销未知项。

上下文接近上限时，Pydantic AI 历史按完整轮次压缩为摘要并保留最近轮次；摘要也扣预算。原始历史在本地加密保存，超过保留周期清理已结束会话正文，不删除用量账本。压缩不结束会话、不清零累计消耗。

单会话预算不足自动结束；每日群或机器人预算不足暂停新调用，次日可继续未结束会话。会话超限按创建时间淘汰最早会话，降低上限立即生效。手动结束、功能停用同样阻止后续模型/工具调用；在途请求费用仍需结算。

搜索/网页来源按本轮实际调用记录，区分内置、外置、两者或未使用。外置只指 DeepSeek 独立 Search/Fetch；它们与模型均使用本群 Key。工具按供应商请求规则计费，token 预算不能代替工具费用上限。内置调用只统计接口返回的记录，接口未返回的内部动作不可推断。

## `/group-discuss admin stats` 命令

### `/group-discuss admin stats` - CHAT

**完整格式**：`/group-discuss admin stats GROUP [today|YYYY-MM-DD|all]`

**所需权限组**：目标群 `group.discuss.admin`（含群 super 继承）或全局 `super`

**参数说明**：GROUP 为群号；日期省略时为 today。查看群内会话、token 消耗、工具次数及未知用量项。

```text
/group-discuss admin stats 123456 today
```

### `/group-discuss admin stats` - GROUP

群聊不可用。请私聊机器人并指定群号。
