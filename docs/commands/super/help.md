# Super 帮助 命令组

[命令目录](../README.md) · [Super 目录](README.md)

本组涉及以下身份组：

- `super`：仅配置 super_user 指定。

仅配置项 `super_user` 指定的账号可使用；通用约定见 [Super 目录](README.md)。

## `/super` 命令

### `/super` - CHAT

**完整格式**：`/super`

**所需权限组**：`super`

查看当前会话可以使用的全部 Super 管理命令，按功能分类展示语法与用途。它与不带分类的 `/super help` 等价。

```text
/super
```

### `/super` - GROUP

**完整格式**：`/super`

**所需权限组**：`super`

查看当前会话可以使用的全部 Super 管理命令，按功能分类展示语法与用途。它与不带分类的 `/super help` 等价。

```text
/super
```

## `/super help` 命令

### `/super help` - CHAT

**完整格式**：`/super help [role|ddl|schedule|request|cost|announce|readonly]`

**所需权限组**：`super`

省略分类时显示全部管理帮助；提供分类名时只显示该组。可选分类为 role、ddl、schedule、request、cost、announce、readonly。

也可以继续指定子命令缩小范围，例如 `/super help ddl edit`；不存在或在当前位置不可用的分类/命令返回“没有可用的对应命令”。

```text
/super help
/super help role
/super help ddl edit
```

### `/super help` - GROUP

**完整格式**：`/super help [role|ddl|schedule|request|cost|announce|readonly]`

**所需权限组**：`super`

省略分类时显示全部管理帮助；提供分类名时只显示该组。可选分类为 role、ddl、schedule、request、cost、announce、readonly。

也可以继续指定子命令缩小范围，例如 `/super help ddl edit`；不存在或在当前位置不可用的分类/命令返回“没有可用的对应命令”。

```text
/super help
/super help role
/super help ddl edit
```
