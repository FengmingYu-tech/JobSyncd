# 调试工具使用指南

## 概述

这个调试工具提供了一个类似 MATLAB Workspace 的可视化调试界面，可以实时查看：
- 变量值和类型
- 函数调用栈
- 执行日志
- 断点状态
- 监视变量

## 启动调试模式

### 方法 1: 使用调试版本的主程序

```bash
cd /Users/u/Library/CloudStorage/GoogleDrive-yufengming1987@gmail.com/マイドライブ/Google\ AI\ Studio/MCP_Practice/JobSync
export PATH="$HOME/.local/bin:$PATH"
uv run python agent/main_debug.py
```

### 方法 2: 在代码中启用调试

在任何 Python 文件中导入调试工具：

```python
from debug_tool import workspace

# 启动调试界面
workspace.start()

# 你的代码...

# 更新变量
workspace.update_variable("my_var", value, "location")

# 停止调试界面
workspace.stop()
```

## 界面说明

调试界面分为以下几个区域：

### 左侧面板

1. **变量 (Variables)**
   - 显示所有已记录的变量
   - 包括变量名、类型、值和位置
   - 变化的变量会高亮显示

2. **监视变量 (Watched)**
   - 显示你特别关注的变量
   - 当这些变量变化时会特别标记

3. **调用栈 (Call Stack)**
   - 显示函数调用层次
   - 从最外层到最内层

### 右侧面板

1. **执行日志 (Execution Log)**
   - 显示程序执行的详细日志
   - 包括函数调用、变量更新、错误等

2. **当前状态 (Current State)**
   - 显示当前执行的函数
   - 当前文件位置
   - 变量数量和调用深度
   - 程序状态（运行/暂停/单步）

3. **断点 (Breakpoints)**
   - 显示所有断点及其状态
   - 显示断点命中次数

## 快捷键

在调试模式下，可以使用以下快捷键（**仅在交互式终端中有效**）：

- **'c'** - 继续执行（如果程序已暂停）
- **'s'** - 单步执行
- **'b'** - 添加断点（会在 `_call_gmail_mcp` 函数处添加）
- **'w'** - 监视变量（会监视 `emails_count` 和 `notion_result`）
- **'p'** - 暂停程序
- **'q'** - 退出调试模式

### ⚠️ 重要提示

**如果快捷键不工作**（常见于 IDE 集成终端或非交互式终端）：

1. **使用代码控制**（推荐）：
   ```python
   from debug_tool import workspace
   
   # 暂停
   workspace.pause()
   
   # 继续
   workspace.resume()
   
   # 单步执行
   workspace.step()
   ```

2. **使用 Ctrl+C**：
   - 如果程序已暂停，按 Ctrl+C 会继续执行
   - 如果程序正在运行，按 Ctrl+C 会退出

3. **在另一个终端控制**：
   打开另一个终端，运行：
   ```bash
   python -c "from debug_tool import workspace; workspace.resume()"
   ```

## 使用示例

### 1. 监视变量

```python
from debug_tool import workspace

workspace.start()
workspace.watch_variable("emails_count")
workspace.watch_variable("notion_result")

# 运行你的代码...
```

### 2. 添加断点

```python
from debug_tool import workspace

workspace.start()

# 在特定函数处添加断点
workspace.add_breakpoint("_call_gmail_mcp")
workspace.add_breakpoint("_call_notion_create")

# 运行你的代码...
# 当执行到这些函数时，程序会自动暂停
```

### 3. 条件断点

```python
from debug_tool import workspace

# 添加条件断点（当 emails_count > 5 时触发）
def condition(*args, **kwargs):
    return workspace.variables.get('emails_count', {}).get('value', 0) > 5

workspace.add_breakpoint("_call_gmail_mcp", condition)
```

### 4. 手动更新变量

```python
from debug_tool import workspace

workspace.start()
workspace.update_variable("status", "Processing", "main")
workspace.update_variable("count", 10, "main")
workspace.update_display()
```

## 调试技巧

1. **监视关键变量**
   - 在程序开始时监视你关心的变量
   - 例如：`workspace.watch_variable("emails_count")`

2. **在关键函数处添加断点**
   - 在 Gmail 获取函数处添加断点，查看获取的邮件
   - 在 Notion 创建函数处添加断点，查看创建的数据

3. **查看调用栈**
   - 了解函数调用关系
   - 找到问题发生的具体位置

4. **查看执行日志**
   - 了解程序的执行流程
   - 查找错误和异常

## 注意事项

1. **性能影响**
   - 调试模式会增加一些性能开销
   - 建议只在需要调试时使用

2. **终端兼容性**
   - 某些终端可能不支持键盘输入处理
   - 如果快捷键不工作，可以直接在代码中调用相应方法

3. **变量显示**
   - 过长的变量值会被截断
   - 复杂对象可能显示为字符串表示

## 故障排除

### 问题：界面不显示

**解决方案：**
- 确保已安装 `rich` 库：`uv add rich`
- 检查终端是否支持 ANSI 颜色代码

### 问题：快捷键不工作

**原因：**
- IDE 的集成终端通常不是交互式终端
- 某些终端不支持 `termios` 和 `select`
- 程序会自动检测并显示警告信息

**解决方案：**

1. **使用代码控制**（最简单）：
   ```python
   from debug_tool import workspace
   
   # 在需要的地方添加
   workspace.pause()   # 暂停
   workspace.resume()  # 继续
   workspace.step()    # 单步
   ```

2. **使用系统终端**：
   - 不要在 IDE 的集成终端中运行
   - 使用系统自带的终端（Terminal.app 或 iTerm2）
   - 运行：`uv run python agent/main_debug.py`

3. **测试键盘输入**：
   ```bash
   uv run python test_keyboard.py
   ```
   如果显示 "✅ 成功读取按键"，说明键盘输入可用

4. **使用 Ctrl+C**：
   - 程序已暂停时，按 Ctrl+C 会继续执行
   - 程序运行中，按 Ctrl+C 会退出

### 问题：变量不更新

**解决方案：**
- 确保在代码中调用了 `workspace.update_variable()`
- 检查变量名是否正确
- 调用 `workspace.update_display()` 刷新界面

## 示例：完整调试流程

```python
from debug_tool import workspace
from workflows.job_sync_workflow import JobSyncWorkflow

# 启动调试界面
workspace.start()

# 添加监视变量
workspace.watch_variable("emails_count")
workspace.watch_variable("notion_result")

# 添加断点
workspace.add_breakpoint("_call_gmail_mcp")
workspace.add_breakpoint("_call_notion_create")

# 运行程序
workflow = JobSyncWorkflow()
result = await workflow.run()

# 停止调试界面
workspace.stop()
```

## 更多功能

调试工具还支持：
- 动态添加/移除断点
- 启用/禁用断点
- 查看断点命中次数
- 查看变量变化历史

详细 API 请参考 `debug_tool.py` 文件。

