# 开发与打包

[返回 README](../README.md)

根目录只保留 AstrBot 发现入口，所有 Python 实现在 `src/`：

| 目录 | 职责 |
| --- | --- |
| `domain/` | 命令表、身份组、作用域、时间和参数规则 |
| `application/` | 统一鉴权/分发、DDL、Super 管理、申请审批和调度 |
| `infrastructure/` | JSON/SQLite 存储、OneBot、模型和消息读取 |
| `presentation/` | 帮助、昵称/群名、详情与卡片图片 |
| `adapters/` | AstrBot 生命周期与事件适配；申请订阅在终止时注销 |
| `tooling/` | 静态检查、图片示例和安装包构建 |

命令鉴权与帮助共用 `domain/commands.py`。管理 DDL 使用独立的明确授权入口，不放宽普通用户或 AI 修改任务的资源限制。角色批量修改原子替换 JSON；DDL 批量修改与调度共用锁，在一次事务内提交。

```sh
python -m src.tooling.check
ruff check src main.py
python -m src.tooling.package
```

构建输出为 `dist/astrbot_plugin_kakobot-v版本.zip`，包含插件代码、README、docs 和中文字体，不包含 examples、工具脚本、运行数据库、密钥或本地设计草稿。GitHub 标签发布工作流沿用现有配置。
