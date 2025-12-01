# 使用 Cursor Browser 进行 OAuth 认证设置指南

本指南说明如何配置 JobSync 项目，使其使用 Cursor IDE 内置的 Browser MCP 进行 OAuth 认证，而不是打开系统默认浏览器。

## 功能说明

传统的 OAuth 认证流程会打开系统默认浏览器，这可能会：
- 打断工作流程
- 在无头服务器环境中无法工作
- 需要手动切换窗口

使用 Cursor Browser MCP 后，所有认证操作都在 Cursor IDE 内部完成，提供更流畅的体验。

## 设置步骤

### 1. 启用 Cursor Browser 认证

在运行认证之前，设置环境变量：

```bash
export USE_CURSOR_BROWSER=true
```

或者在 `.env` 文件中添加：

```env
USE_CURSOR_BROWSER=true
```

### 2. 在 Cursor Agent 中运行认证

当您运行 `agent/main.py` 或首次需要 Gmail 认证时，系统会：

1. **生成 OAuth URL**：系统会显示一个授权 URL
2. **提示使用 Cursor Browser**：系统会提示您在 Cursor agent 中使用 browser 工具

### 3. 在 Cursor Agent 中完成认证

当看到提示时，在 Cursor agent 中执行以下步骤：

#### 步骤 1: 导航到授权 URL

使用 `browser_navigate` 工具打开显示的授权 URL：

```
browser_navigate(url="<显示的授权URL>")
```

#### 步骤 2: 查看页面状态

使用 `browser_snapshot` 查看当前页面：

```
browser_snapshot()
```

#### 步骤 3: 完成登录和授权

根据页面内容，使用以下工具完成认证：

- **输入邮箱**：使用 `browser_type` 在邮箱输入框中输入您的 Gmail 地址
- **点击按钮**：使用 `browser_click` 点击"下一步"、"允许"等按钮
- **输入密码**：使用 `browser_type` 输入密码（如果需要）

#### 步骤 4: 等待回调

认证完成后，系统会自动：
- 接收授权码
- 交换访问令牌
- 保存凭据到 `token.json`

## 示例：在 Cursor Agent 中的完整流程

当您看到以下输出时：

```
🌐 使用 Cursor Browser 进行 OAuth 认证...
📋 步骤 1: 获取 OAuth 授权 URL...

======================================================================
🌐 请在 Cursor agent 中使用以下信息完成认证：
======================================================================

授权 URL: https://accounts.google.com/o/oauth2/auth?...
回调端口: 8080

📝 在 Cursor agent 中执行以下操作：
1. 使用 browser_navigate 工具打开上面的授权 URL
2. 使用 browser_snapshot 查看页面状态
3. 使用 browser_click 和 browser_type 完成登录和授权
4. 等待认证完成...
======================================================================
```

在 Cursor agent 中执行：

```python
# 1. 导航到授权页面
browser_navigate(url="https://accounts.google.com/o/oauth2/auth?...")

# 2. 查看页面
browser_snapshot()

# 3. 根据页面内容进行操作
# 例如：输入邮箱
browser_type(element="邮箱输入框", ref="<从snapshot获取的ref>", text="your.email@gmail.com")

# 点击下一步
browser_click(element="下一步按钮", ref="<从snapshot获取的ref>")

# 继续查看和操作，直到完成授权
browser_snapshot()
# ... 继续操作直到看到成功页面
```

## 回退机制

如果 Cursor Browser 认证失败或不可用，系统会自动回退到传统的系统浏览器方式。

## 技术细节

### 工作原理

1. **OAuth Flow 初始化**：`browser_oauth.py` 模块创建 OAuth flow 并生成授权 URL
2. **本地回调服务器**：启动一个本地 HTTP 服务器监听 OAuth 回调
3. **Cursor Browser 交互**：在 Cursor Browser 中完成用户认证
4. **令牌交换**：使用接收到的授权码交换访问令牌

### 文件结构

- `agent/browser_oauth.py`：Cursor Browser OAuth 辅助模块
- `agent/gmail_client.py`：修改后的 Gmail 客户端，支持选择认证方式

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `USE_CURSOR_BROWSER` | 是否使用 Cursor Browser 进行认证 | `false` |

## 故障排除

### 问题：认证超时

**原因**：在 Cursor Browser 中完成认证的时间过长

**解决**：
- 确保在 5 分钟内完成认证流程
- 如果超时，系统会自动回退到系统浏览器方式

### 问题：无法找到 browser_oauth 模块

**原因**：模块导入失败

**解决**：
- 确保 `agent/browser_oauth.py` 文件存在
- 检查 Python 路径配置

### 问题：回调服务器端口被占用

**原因**：端口 8080 已被其他程序使用

**解决**：
- 系统会自动尝试其他端口（49256, 8000）
- 或者手动修改 `browser_oauth.py` 中的端口配置

## 优势

✅ **集成体验**：所有操作在 Cursor IDE 内部完成  
✅ **无窗口切换**：不需要切换到外部浏览器  
✅ **服务器友好**：适合在无头服务器环境中使用  
✅ **自动化友好**：更容易在自动化流程中集成  

## 注意事项

⚠️ **首次使用**：首次使用时需要手动在 Cursor agent 中完成认证流程  
⚠️ **安全性**：确保在安全的环境中运行，避免授权 URL 泄露  
⚠️ **Token 保存**：认证成功后，token 会保存在 `agent/token.json` 中，后续使用无需重新认证  

## 相关文件

- `agent/browser_oauth.py` - Cursor Browser OAuth 实现
- `agent/gmail_client.py` - Gmail 客户端（已更新支持 Cursor Browser）
- `SETUP_ENV.md` - 完整的项目设置指南





