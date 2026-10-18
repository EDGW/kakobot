# 开发与打包

[返回 README](../README.md)

根目录只保留 AstrBot 发现入口，所有 Python 实现在 `src/`：

| 目录 | 职责 |
| --- | --- |
| `domain/` | 命令表、身份组、作用域、时间和参数规则 |
| `application/` | 运行时组装、统一鉴权/分发、用户会话协调 |
| `application/deadlines/` | DDL 创建、自动分析、解析、修改和提醒调度 |
| `application/roles/` | 本人身份查询和 Super 身份组管理 |
| `application/messaging/` | 广播与聊天总结 |
| `application/management/` | Super 申请审批和费用查询 |
| `infrastructure/storage/` | JSON/SQLite 基础存储、审计、申请、用量和启动迁移 |
| `infrastructure/storage/deadlines/` | DDL 任务、管理查询和个人默认提醒配置 |
| `infrastructure/storage/access/` | 身份组和只读群配置 |
| `infrastructure/storage/broadcasts/` | 广播接收会话、拒收偏好和更新文案读取 |
| `infrastructure/messaging/` | OneBot 收发、消息展开和输出分段/合并转发 |
| `infrastructure/model.py` | 模型请求与用量记录 |
| `presentation/` | 帮助、昵称/群名、费用和广播格式 |
| `presentation/deadlines/` | DDL 详情文字和本地卡片图片 |
| `adapters/` | AstrBot 生命周期与事件适配；申请订阅在终止时注销 |
| `tooling/` | 静态检查、图片示例和安装包构建 |

命令鉴权与帮助共用 `domain/commands.py`。管理 DDL 使用独立的明确授权入口，不放宽普通用户或 AI 修改任务的资源限制。角色批量修改原子替换 JSON；DDL 批量修改与调度共用锁，在一次事务内提交。

各层按职责建立子包，包入口仅说明用途，调用方直接导入实际模块。领域层只保留共享规则与值对象，不依赖应用、存储或展示实现。启动组装集中在 `application/runtime.py`，命令分发集中在 `application/dispatcher.py`。

默认广播内容保留在 `src/UPDATE.md`，由 `infrastructure/storage/broadcasts/updates.py` 每次读取。字体位于 `assets/fonts/`；移动渲染或读取模块时须同步校验资源定位。打包递归收集所有业务 Python 子包，并显式包含更新文案。

```sh
python -m src.tooling.check
ruff check src main.py
python -m src.tooling.package
```

构建输出为 `dist/astrbot_plugin_kakobot-v版本.zip`，包含插件代码、README、docs 和中文字体，不包含 examples、工具脚本、运行数据库、密钥或本地设计草稿。GitHub 标签发布工作流沿用现有配置。

命令文档中，一个 Markdown 文件对应一组功能，在每个命令下分别说明 CHAT、GROUP 的完整格式、所需权限组和行为。普通命令放在 `docs/commands/`，Super 命令放在 `docs/commands/super/`；各目录的 README 维护功能索引。
